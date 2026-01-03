from . import bp
from flask import jsonify, request, render_template
from flask import session
from utils.db import get_db
from blueprints.auth.utils import login_required
from datetime import date, timedelta, datetime

# ==================================================================================
# ATTENDANCE BLUEPRINT - ALL QUERIES USE DATE(check_in_time)
# ==================================================================================
# IMPORTANT: All attendance APIs derive dates from DATE(check_in_time).
# Legacy 'date' column in attendance table is IGNORED.
# 
# Calendar & Summary Logic:
# - Generates ALL dates in month (not just attendance records)
# - Checks leaves table for approved leaves
# - Checks holidays table for company holidays
# - Applies priority: leave > holiday > weekend > attendance > absent
# 
# This ensures comprehensive calendar views with automatic leave integration.
# ==================================================================================

# --------------------------------------------------
# Normalize static paths
# --------------------------------------------------
def norm(path):
    if not path:
        return None
    if path.startswith("/"):
        return path
    if "static/" in path:
        return "/" + path[path.find("static/"):]
    return "/static/" + path


# --------------------------------------------------
# ATTENDANCE PAGE  (UI page)
# --------------------------------------------------
@bp.route("/")
@login_required
def attendance_logs():
    return render_template("attendance.html")


# --------------------------------------------------
# USER LIST  (for username filter dropdown)
# --------------------------------------------------
@bp.route("/api/usernames")
@login_required
def api_usernames():
    db = get_db()
    cur = db.cursor(dictionary=True)

    # EMPLOYEE → only self
    if session.get("role") == "employee":
        cur.execute(
            "SELECT id, full_name FROM employees WHERE id = %s",
            (session.get("employee_id"),)
        )
    else:
        # ADMIN / HR → all
        cur.execute("SELECT id, full_name FROM employees ORDER BY full_name ASC")

    rows = cur.fetchall()

    cur.close()
    return jsonify({"status": "ok", "users": rows})


# --------------------------------------------------
# ATTENDANCE TABLE DATA API
# --------------------------------------------------
@bp.route("/api/attendance")
@login_required
def api_attendance():
    date = request.args.get("date")
    user = request.args.get("user")

    role = session.get("role")
    emp_id = session.get("employee_id")

    db = get_db()
    cur = db.cursor(dictionary=True)

    base_query = """
        SELECT 
            a.id,
            a.employee_id,
            DATE(a.check_in_time) AS date,
            a.check_in_time,
            a.check_out_time,
            a.working_hours,
            a.status,
            e.full_name AS name,
            e.photo_path AS photo,
            (
                SELECT image_path 
                FROM recognition_logs
                WHERE employee_id = a.employee_id
                  AND DATE(timestamp) = DATE(a.check_in_time)
                ORDER BY id DESC
                LIMIT 1
            ) AS snapshot,
            (
                SELECT COUNT(*) 
                FROM leaves l 
                WHERE l.employee_id = a.employee_id 
                  AND l.status = 'approved'
                  AND DATE(a.check_in_time) BETWEEN l.start_date AND l.end_date
            ) AS is_on_leave,
            (
                SELECT COUNT(*) 
                FROM holidays h 
                WHERE h.holiday_date = DATE(a.check_in_time)
            ) AS is_holiday
        FROM attendance a
        JOIN employees e ON e.id = a.employee_id
        WHERE 1=1
    """

    params = []

    # 🔒 EMPLOYEE → ONLY OWN DATA
    if role == "employee":
        base_query += " AND a.employee_id = %s"
        params.append(emp_id)

    # 👑 ADMIN / HR FILTERS
    if role in ["admin", "hr"]:
        if user:
            base_query += " AND e.full_name = %s"
            params.append(user)

    if date:
        base_query += " AND DATE(a.check_in_time) = %s"
        params.append(date)

    base_query += " ORDER BY DATE(a.check_in_time) DESC, a.check_in_time DESC"

    cur.execute(base_query, tuple(params))
    rows = cur.fetchall()
    cur.close()

    for r in rows:
        if r.get("snapshot"):
            r["snapshot"] = norm(r["snapshot"])
        if r.get("photo"):
            r["photo"] = norm(r["photo"])
        
        # Override status if on approved leave
        if r.get("is_on_leave") and r["is_on_leave"] > 0:
            r["status"] = "on_leave"
            r["check_in_time"] = None
            r["check_out_time"] = None
            r["working_hours"] = None
        elif r.get("is_holiday") and r["is_holiday"] > 0:
            r["status"] = "holiday"

    return jsonify({"status": "ok", "records": rows})


# --------------------------------------------------
# MONTHLY SUMMARY API (Employee-specific monthly stats)
# Used by Reports page for employee analysis section
# Counts present/leave/absent/holiday days for selected month
# Uses DATE(check_in_time) with leaves & holidays integration
# --------------------------------------------------
@bp.route("/api/monthly-summary")
@login_required
def api_monthly_summary():
    """Get monthly attendance summary for employee"""
    from datetime import datetime
    
    # Accept year and month as separate params or combined month param
    year = request.args.get("year", type=int)
    month_num = request.args.get("month", type=int)
    month_param = request.args.get("month")  # Fallback for YYYY-MM format
    employee_name = request.args.get("employee_name", "").strip()
    
    # Format month
    if year and month_num:
        month = f"{year}-{str(month_num).zfill(2)}"
    elif month_param:
        month = month_param
    else:
        month = datetime.now().strftime("%Y-%m")
    
    role = session.get("role")
    employee_id = None
    
    # Get employee_id based on role and filters
    if employee_name and role in ['admin', 'hr']:
        # Admin/HR viewing specific employee by name
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT id 
            FROM employees 
            WHERE full_name = %s
        """, (employee_name,))
        result = cur.fetchone()
        cur.close()
        
        if result:
            employee_id = result['id']
        else:
            return jsonify({"status": "error", "message": "Employee not found"}), 404
    else:
        # Regular employee viewing own data
        employee_id = session.get('employee_id')
    
    if not employee_id:
        return jsonify({"status": "error", "message": "Employee ID required"}), 400
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # DEBUG: Log query parameters
    print(f"🔍 Monthly Summary Query - employee_id: {employee_id}, year: {year}, month_num: {month_num}, employee_name: {employee_name}")
    
    # Calculate summary - FIXED to use DATE(check_in_time)
    cur.execute("""
        SELECT 
            COUNT(DISTINCT CASE 
                WHEN a.status IN ('present', 'late', 'check-in', 'check-out') 
                AND NOT EXISTS (
                    SELECT 1 FROM leaves l 
                    WHERE l.employee_id = %s 
                      AND l.status = 'approved' 
                      AND DATE(a.check_in_time) BETWEEN l.start_date AND l.end_date
                )
                AND NOT EXISTS (
                    SELECT 1 FROM holidays h 
                    WHERE h.holiday_date = DATE(a.check_in_time)
                )
                THEN DATE(a.check_in_time) 
            END) AS present_days,
            COUNT(DISTINCT CASE 
                WHEN EXISTS (
                    SELECT 1 FROM leaves l 
                    WHERE l.employee_id = %s 
                      AND l.status = 'approved' 
                      AND DATE(a.check_in_time) BETWEEN l.start_date AND l.end_date
                ) THEN DATE(a.check_in_time) 
            END) AS leave_days,
            COUNT(DISTINCT CASE 
                WHEN a.status = 'absent' 
                  AND NOT EXISTS (
                      SELECT 1 FROM leaves l 
                      WHERE l.employee_id = %s 
                        AND l.status = 'approved' 
                        AND DATE(a.check_in_time) BETWEEN l.start_date AND l.end_date
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM holidays h 
                      WHERE h.holiday_date = DATE(a.check_in_time)
                  )
                THEN DATE(a.check_in_time) 
            END) AS absent_days,
            COALESCE(SUM(a.working_hours), 0) AS total_hours,
            COUNT(DISTINCT CASE 
                WHEN EXISTS (
                    SELECT 1 FROM holidays h 
                    WHERE h.holiday_date = DATE(a.check_in_time)
                ) THEN DATE(a.check_in_time) 
            END) AS holiday_days
        FROM attendance a
        WHERE a.employee_id = %s
          AND YEAR(a.check_in_time) = %s
          AND MONTH(a.check_in_time) = %s
    """, (employee_id, employee_id, employee_id, employee_id, year, month_num))
    
    summary = cur.fetchone()
    
    # DEBUG: Log results
    print(f"🔍 Summary Results: {summary}")
    
    # Get employee details
    cur.execute("SELECT full_name, email FROM employees WHERE id = %s", (employee_id,))
    emp = cur.fetchone()
    
    cur.close()
    
    return jsonify({
        "status": "ok",
        "employee": emp,
        "month": month,
        "present_days": summary['present_days'] or 0,
        "leave_days": summary['leave_days'] or 0,
        "absent_days": summary['absent_days'] or 0,
        "holiday_days": summary['holiday_days'] or 0,
        "total_hours": float(summary['total_hours'] or 0)
    })


# --------------------------------------------------
# CALENDAR VIEW API (Employee monthly calendar with ALL dates)
# Used by Reports page for visual attendance calendar
# IMPORTANT: Generates ALL dates in month (not just attendance records)
# Integrates approved leaves, company holidays, and weekends automatically
# Priority: leave > holiday > weekend > attendance > absent
# --------------------------------------------------
@bp.route("/api/calendar")
@login_required
def api_calendar():
    """Get calendar view of attendance for a month with comprehensive date coverage"""
    from datetime import datetime
    
    year = request.args.get('year', type=int)
    month_num = request.args.get('month', type=int)
    employee_name = request.args.get("employee_name", "").strip()
    
    if not year or not month_num:
        # Default to current month
        now = datetime.now()
        year = now.year
        month_num = now.month
    
    month = f"{year}-{month_num:02d}"
    
    role = session.get("role")
    employee_id = None
    
    # Get employee_id based on role and filters
    if employee_name and role in ['admin', 'hr']:
        # Admin/HR viewing specific employee by name
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT id 
            FROM employees 
            WHERE full_name = %s
        """, (employee_name,))
        result = cur.fetchone()
        cur.close()
        
        if result:
            employee_id = result['id']
        else:
            return jsonify({"status": "error", "message": "Employee not found"}), 404
    else:
        # Regular employee viewing own data
        employee_id = session.get('employee_id')
    
    if not employee_id:
        # Admin/HR without specific employee - return empty calendar with message
        if role in ['admin', 'hr']:
            return jsonify({
                "status": "ok",
                "month": month,
                "calendar": [],
                "message": "Please select an employee to view calendar"
            })
        return jsonify({"status": "error", "message": "Employee ID required"}), 400
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # DEBUG: Log query parameters
    print(f"🔍 Calendar Query - employee_id: {employee_id}, month: {month}, year: {year}, month_num: {month_num}")
    
    # Get attendance records for the month
    cur.execute("""
        SELECT 
            DATE(a.check_in_time) AS date,
            a.check_in_time,
            a.check_out_time,
            a.working_hours,
            a.status AS attendance_status
        FROM attendance a
        WHERE a.employee_id = %s
          AND YEAR(a.check_in_time) = %s
          AND MONTH(a.check_in_time) = %s
    """, (employee_id, year, month_num))
    
    attendance_records = {row['date'].strftime('%Y-%m-%d'): row for row in cur.fetchall()}
    
    # Get approved leaves for this employee in this month
    cur.execute("""
        SELECT start_date, end_date, leave_type 
        FROM leaves 
        WHERE employee_id = %s 
          AND status = 'approved'
          AND (
              (YEAR(start_date) = %s AND MONTH(start_date) = %s)
              OR (YEAR(end_date) = %s AND MONTH(end_date) = %s)
              OR (start_date <= %s AND end_date >= %s)
          )
    """, (employee_id, year, month_num, year, month_num, 
          f"{year}-{month_num:02d}-01", f"{year}-{month_num:02d}-01"))
    
    leave_records = cur.fetchall()
    leave_dates = set()
    for leave in leave_records:
        current_date = leave['start_date']
        while current_date <= leave['end_date']:
            if current_date.year == year and current_date.month == month_num:
                leave_dates.add(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
    
    # Get holidays for this month
    cur.execute("""
        SELECT holiday_date, holiday_name 
        FROM holidays 
        WHERE YEAR(holiday_date) = %s AND MONTH(holiday_date) = %s
    """, (year, month_num))
    
    holiday_records = {row['holiday_date'].strftime('%Y-%m-%d'): row['holiday_name'] for row in cur.fetchall()}
    
    # Generate all dates in the month
    from datetime import date, timedelta
    calendar_data = []
    days_in_month = (date(year + (1 if month_num == 12 else 0), (month_num % 12) + 1, 1) - timedelta(days=1)).day
    
    for day in range(1, days_in_month + 1):
        current_date = date(year, month_num, day)
        date_str = current_date.strftime('%Y-%m-%d')
        day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
        
        # Determine final status with priority: leave > holiday > weekend > attendance > absent
        if date_str in leave_dates:
            final_status = 'on_leave'
            attendance_status = 'on_leave'
        elif date_str in holiday_records:
            final_status = 'holiday'
            attendance_status = 'holiday'
        elif day_of_week in [5, 6]:  # Saturday=5, Sunday=6
            final_status = 'weekend'
            attendance_status = 'weekend'
        elif date_str in attendance_records:
            att = attendance_records[date_str]
            attendance_status = att['attendance_status']
            final_status = attendance_status
        else:
            # No attendance record - mark as absent
            final_status = 'absent'
            attendance_status = 'absent'
        
        calendar_data.append({
            'date': date_str,
            'attendance_status': attendance_status,
            'final_status': final_status,
            'holiday_name': holiday_records.get(date_str, None),
            'check_in_time': attendance_records[date_str]['check_in_time'] if date_str in attendance_records else None,
            'check_out_time': attendance_records[date_str]['check_out_time'] if date_str in attendance_records else None,
            'working_hours': float(attendance_records[date_str]['working_hours']) if date_str in attendance_records and attendance_records[date_str]['working_hours'] else None
        })
    
    # DEBUG: Log results
    print(f"🔍 Calendar Results - Generated {len(calendar_data)} days")
    print(f"🔍 Attendance records: {len(attendance_records)}, Leaves: {len(leave_dates)}, Holidays: {len(holiday_records)}")
    
    cur.close()
    
    return jsonify({
        "status": "ok",
        "month": month,
        "calendar": calendar_data
    })

