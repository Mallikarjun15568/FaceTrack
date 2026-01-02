from . import bp
from flask import jsonify, request, render_template
from flask import session
from utils.db import get_db
from blueprints.auth.utils import login_required

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
            a.date,
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
                  AND DATE(timestamp) = a.date
                ORDER BY id DESC
                LIMIT 1
            ) AS snapshot,
            (
                SELECT COUNT(*) 
                FROM leaves l 
                WHERE l.employee_id = a.employee_id 
                  AND l.status = 'approved'
                  AND a.date BETWEEN l.start_date AND l.end_date
            ) AS is_on_leave,
            (
                SELECT COUNT(*) 
                FROM holidays h 
                WHERE h.holiday_date = a.date
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
        base_query += " AND a.date = %s"
        params.append(date)

    base_query += " ORDER BY a.date DESC, a.check_in_time ASC"

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
# MONTHLY SUMMARY API
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
    
    # Calculate summary
    cur.execute("""
        SELECT 
            COUNT(DISTINCT CASE WHEN a.status IN ('present', 'late') THEN a.date END) AS present_days,
            COUNT(DISTINCT CASE 
                WHEN EXISTS (
                    SELECT 1 FROM leaves l 
                    WHERE l.employee_id = %s 
                      AND l.status = 'approved' 
                      AND a.date BETWEEN l.start_date AND l.end_date
                ) THEN a.date 
            END) AS leave_days,
            COUNT(DISTINCT CASE 
                WHEN a.status = 'absent' 
                  AND NOT EXISTS (
                      SELECT 1 FROM leaves l 
                      WHERE l.employee_id = %s 
                        AND l.status = 'approved' 
                        AND a.date BETWEEN l.start_date AND l.end_date
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM holidays h 
                      WHERE h.holiday_date = a.date
                  )
                THEN a.date 
            END) AS absent_days,
            COALESCE(SUM(a.working_hours), 0) AS total_hours,
            COUNT(DISTINCT CASE 
                WHEN EXISTS (
                    SELECT 1 FROM holidays h 
                    WHERE h.holiday_date = a.date
                ) THEN a.date 
            END) AS holiday_days
        FROM attendance a
        WHERE a.employee_id = %s
          AND DATE_FORMAT(a.date, '%%Y-%%m') = %s
    """, (employee_id, employee_id, employee_id, month))
    
    summary = cur.fetchone()
    
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
# CALENDAR VIEW API
# --------------------------------------------------
@bp.route("/api/calendar")
@login_required
def api_calendar():
    """Get calendar view of attendance for a month"""
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
    
    # Get all dates in month with status
    cur.execute("""
        SELECT 
            a.date,
            a.check_in_time,
            a.check_out_time,
            a.working_hours,
            a.status AS attendance_status,
            CASE 
                WHEN EXISTS (
                    SELECT 1 FROM leaves l 
                    WHERE l.employee_id = %s 
                      AND l.status = 'approved' 
                      AND a.date BETWEEN l.start_date AND l.end_date
                ) THEN 'on_leave'
                WHEN EXISTS (
                    SELECT 1 FROM holidays h 
                    WHERE h.holiday_date = a.date
                ) THEN 'holiday'
                WHEN DAYOFWEEK(a.date) IN (1, 7) THEN 'weekend'
                ELSE a.status
            END AS final_status,
            (SELECT holiday_name FROM holidays WHERE holiday_date = a.date LIMIT 1) AS holiday_name
        FROM attendance a
        WHERE a.employee_id = %s
          AND DATE_FORMAT(a.date, '%%Y-%%m') = %s
        ORDER BY a.date ASC
    """, (employee_id, employee_id, month))
    
    calendar_data = cur.fetchall()
    
    # DEBUG: Log results
    print(f"🔍 Calendar Results - Found {len(calendar_data)} records")
    if len(calendar_data) > 0:
        print(f"🔍 First record: {calendar_data[0]}")
    
    cur.close()
    
    return jsonify({
        "status": "ok",
        "month": month,
        "calendar": calendar_data
    })

