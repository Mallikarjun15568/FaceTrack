from utils.email_service import EmailService
from utils.db import get_db
from flask import current_app, render_template, request, session, jsonify
from datetime import datetime, date, timedelta
from utils.logger import logger
from . import bp

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
def attendance_logs():
    return render_template("attendance.html")


# --------------------------------------------------
# USER LIST  (for username filter dropdown)
# --------------------------------------------------
@bp.route("/api/usernames")
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
                        DATE(COALESCE(a.check_in_time, a.date)) AS date,
                        a.check_in_time,
                        a.check_out_time,
                        a.working_hours,
                        a.status,
                        e.full_name AS name,
                        e.photo AS photo,
                        (
                                SELECT image_path 
                                FROM recognition_logs
                                WHERE employee_id = a.employee_id
                                    AND DATE(timestamp) = DATE(COALESCE(a.check_in_time, a.date))
                                ORDER BY id DESC
                                LIMIT 1
                        ) AS snapshot,
                        (
                                SELECT COUNT(*) 
                                FROM leaves l 
                                WHERE l.employee_id = a.employee_id 
                                    AND l.status = 'approved'
                                    AND DATE(COALESCE(a.check_in_time, a.date)) BETWEEN l.start_date AND l.end_date
                        ) AS is_on_leave,
                        (
                                SELECT COUNT(*) 
                                FROM holidays h 
                                WHERE h.holiday_date = DATE(COALESCE(a.check_in_time, a.date))
                        ) AS is_holiday
        FROM attendance a
        JOIN employees e ON e.id = a.employee_id AND e.status = 'active'
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
        base_query += " AND DATE(COALESCE(a.check_in_time, a.date)) = %s"
        params.append(date)

    base_query += " ORDER BY DATE(COALESCE(a.check_in_time, a.date)) DESC, a.check_in_time DESC"

    cur.execute(base_query, tuple(params))
    rows = cur.fetchall()
    cur.close()

    for r in rows:
        if r.get("snapshot"):
            r["snapshot"] = norm(r["snapshot"])
        if r.get("photo"):
            r["photo"] = norm(r["photo"])
        
        # Convert datetime objects to string format (YYYY-MM-DD HH:MM:SS) without timezone
        if r.get("check_in_time") and hasattr(r["check_in_time"], 'strftime'):
            r["check_in_time"] = r["check_in_time"].strftime('%Y-%m-%d %H:%M:%S')
        if r.get("check_out_time") and hasattr(r["check_out_time"], 'strftime'):
            r["check_out_time"] = r["check_out_time"].strftime('%Y-%m-%d %H:%M:%S')
        
        # Override status if on approved leave
        if r.get("is_on_leave") and r["is_on_leave"] > 0:
            r["status"] = "on_leave"
            r["check_in_time"] = None
            r["check_out_time"] = None
            r["working_hours"] = None
        elif r.get("is_holiday") and r["is_holiday"] > 0:
            r["status"] = "holiday"

    # Check for missing checkouts and send email (only after office hours)
    try:
        check_missing_checkouts()
    except Exception as e:
        current_app.logger.error(f"Error checking missing checkouts: {str(e)}")

    return jsonify({"status": "ok", "records": rows})


# --------------------------------------------------
# CHECK MISSING CHECKOUTS & SEND EMAIL (End of Day)
# --------------------------------------------------
def check_missing_checkouts():
    """Check for employees who checked in but didn't check out by end of day"""
    from datetime import datetime
    current_time = datetime.now()
    
    # Only check after 6 PM (configurable checkout time)
    checkout_hour = 18  # 6 PM
    if current_time.hour < checkout_hour:
        return  # Too early, don't check
    
    # Only check once per day (use a simple flag)
    today = current_time.date()
    flag_key = f"checkout_email_sent_{today}"
    
    # Check if we already sent emails today
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT setting_value FROM settings WHERE setting_key = %s", (flag_key,))
    flag_exists = cur.fetchone()
    
    if flag_exists:
        return  # Already sent emails today
    
    # Find employees with check-in but no check-out for today
    cur.execute("""
        SELECT a.employee_id, e.full_name, e.email
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE DATE(a.check_in_time) = CURDATE()
            AND a.check_out_time IS NULL
            AND a.status = 'check-in'
            AND e.email IS NOT NULL
            AND e.email != ''
            AND e.status = 'active'
    """)
    
    missing_checkouts = cur.fetchall()
    
    if not missing_checkouts:
        # No missing checkouts, but mark as checked to avoid repeated checks
        cur.execute("INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s)", (flag_key, "checked"))
        db.commit()
        return
    
    # Send email to each employee
    email_service = EmailService(current_app)
    sent_count = 0
    
    for record in missing_checkouts:
        employee_name = record[1]
        employee_email = record[2]
        
        try:
            email_service.send_missing_checkout_notification(employee_email, employee_name)
            sent_count += 1
        except Exception as e:
            current_app.logger.error(f"Failed to send checkout notification to {employee_email}: {str(e)}")
    
    # Mark as sent for today
    cur.execute("INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s)", (flag_key, f"sent_{sent_count}"))
    db.commit()
    
    current_app.logger.info(f"Sent {sent_count} missing checkout notifications")
    cur.close()


# --------------------------------------------------
# MONTHLY SUMMARY API (Employee-specific monthly stats)
# Used by Reports page for employee analysis section
# Counts present/leave/absent/holiday days for selected month
# Uses DATE(check_in_time) with leaves & holidays integration
# --------------------------------------------------
@bp.route("/api/monthly-summary")
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
    
    # Calculate monthly summary using same logic as calendar
    # Get all dates in the month and classify each day
    from datetime import date, timedelta
    
    # Calculate days in month
    if month_num == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month_num + 1, 1)
    days_in_month = (next_month - timedelta(days=1)).day
    
    # Get attendance records for the month
    cur.execute("""
        SELECT DATE(COALESCE(a.check_in_time, a.date)) as attendance_date,
               a.status, a.working_hours
        FROM attendance a
        WHERE a.employee_id = %s
          AND YEAR(COALESCE(a.check_in_time, a.date)) = %s
          AND MONTH(COALESCE(a.check_in_time, a.date)) = %s
    """, (employee_id, year, month_num))
    
    attendance_records = {row['attendance_date']: row for row in cur.fetchall()}
    
    # Get approved leaves for the month
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
          f"{year}-{month_num:02d}-01", f"{year}-{month_num:02d}-{days_in_month:02d}"))
    
    leave_records = cur.fetchall()
    leave_dates = set()
    for leave in leave_records:
        try:
            current_date = leave['start_date']
            end_date = leave['end_date']
            if current_date and end_date:
                while current_date <= end_date:
                    if current_date.year == year and current_date.month == month_num:
                        leave_dates.add(current_date)
                    current_date += timedelta(days=1)
        except Exception as e:
            print(f"Error processing leave dates: {e}")
            continue
    
    # Get holidays for the month
    cur.execute("""
        SELECT holiday_date 
        FROM holidays 
        WHERE YEAR(holiday_date) = %s AND MONTH(holiday_date) = %s
    """, (year, month_num))
    
    holiday_dates = {row['holiday_date'] for row in cur.fetchall()}
    
    # Calculate summary by checking each day
    present_days = 0
    leave_days = 0
    absent_days = 0
    holiday_days = 0
    total_hours = 0.0
    
    for day in range(1, days_in_month + 1):
        current_date = date(year, month_num, day)
        day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
        
        # Check priority: leave > holiday > weekend > attendance > absent
        if current_date in leave_dates:
            leave_days += 1
        elif current_date in holiday_dates:
            holiday_days += 1
        elif day_of_week >= 5:  # Saturday/Sunday
            continue  # Skip weekends in count
        elif current_date in attendance_records:
            # Has attendance record
            record = attendance_records[current_date]
            if record['status'] in ['present', 'late', 'check-in', 'check-out']:
                present_days += 1
                total_hours += float(record['working_hours'] or 0)
            else:
                absent_days += 1
        else:
            # No record = absent
            absent_days += 1
    
    # DEBUG: Log results
    print(f"🔍 Summary Results: present_days={present_days}, leave_days={leave_days}, absent_days={absent_days}, holiday_days={holiday_days}, total_hours={total_hours}")
    
    # Get employee details
    cur.execute("SELECT full_name, email FROM employees WHERE id = %s", (employee_id,))
    emp = cur.fetchone()
    
    cur.close()
    
    return jsonify({
        "status": "ok",
        "employee": emp,
        "month": month,
        "present_days": present_days,
        "leave_days": leave_days,
        "absent_days": absent_days,
        "holiday_days": holiday_days,
        "total_hours": total_hours
    })


# --------------------------------------------------
# CALENDAR VIEW API (Employee monthly calendar with ALL dates)
# Used by Reports page for visual attendance calendar
# IMPORTANT: Generates ALL dates in month (not just attendance records)
# Integrates approved leaves, company holidays, and weekends automatically
# Priority: leave > holiday > weekend > attendance > absent
# --------------------------------------------------
@bp.route("/api/calendar")
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
            DATE(COALESCE(a.check_in_time, a.date)) AS date,
            a.check_in_time,
            a.check_out_time,
            a.working_hours,
            a.status AS attendance_status
        FROM attendance a
        WHERE a.employee_id = %s
          AND YEAR(COALESCE(a.check_in_time, a.date)) = %s
          AND MONTH(COALESCE(a.check_in_time, a.date)) = %s
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
        try:
            current_date = leave['start_date']
            end_date = leave['end_date']
            if current_date and end_date:
                while current_date <= end_date:
                    if current_date.year == year and current_date.month == month_num:
                        leave_dates.add(current_date.strftime('%Y-%m-%d'))
                    current_date += timedelta(days=1)
        except Exception as e:
            print(f"Error processing leave dates: {e}, leave: {leave}")
            continue
    
    # Get holidays for this month
    cur.execute("""
        SELECT holiday_date, holiday_name 
        FROM holidays 
        WHERE YEAR(holiday_date) = %s AND MONTH(holiday_date) = %s
    """, (year, month_num))
    
    holiday_records = {row['holiday_date'].strftime('%Y-%m-%d'): row['holiday_name'] for row in cur.fetchall()}
    
    # Generate all dates in the month
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


# --------------------------------------------------
# COMPLETE CHECK-OUT API (ADMIN/HR ONLY)
# --------------------------------------------------
@bp.route("/api/complete_checkout/<int:attendance_id>", methods=["POST"])
def api_complete_checkout(attendance_id):
    # Only allow admin/hr to complete check-outs
    if session.get("role") not in ["admin", "hr"]:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    db = get_db()
    cur = db.cursor(dictionary=True)

    try:
        # Get the attendance record with employee details
        cur.execute("""
            SELECT a.id, a.employee_id, a.check_in_time, a.check_out_time, a.status,
                   e.full_name, e.email
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            WHERE a.id = %s
        """, (attendance_id,))

        record = cur.fetchone()
        if not record:
            return jsonify({"status": "error", "message": "Attendance record not found"}), 404

        if record["check_out_time"] is not None:
            return jsonify({"status": "error", "message": "Check-out already completed"}), 400

        if record["check_in_time"] is None:
            return jsonify({"status": "error", "message": "No check-in time found"}), 400

        # Prefer the latest recognition timestamp on the same day as the attendance
        # (so checkout reflects the actual last recognition that day). Fall back to now.
        check_in_time = record["check_in_time"]
        if isinstance(check_in_time, str):
            check_in_time = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S')

        check_out_time = None
        try:
            cur.execute("""
                SELECT timestamp FROM recognition_logs
                WHERE employee_id = %s AND DATE(timestamp) = DATE(%s)
                ORDER BY id DESC LIMIT 1
            """, (record['employee_id'], check_in_time))
            rec = cur.fetchone()
            if rec and rec.get('timestamp'):
                check_out_time = rec['timestamp']
        except Exception:
            check_out_time = None

        if not check_out_time:
            # No same-day recognition found — fallback to company-configured checkout time
            try:
                checkout_conf = current_app.config.get('CHECKOUT_TIME')
                if checkout_conf:
                    try:
                        parsed_time = datetime.strptime(str(checkout_conf), '%H:%M').time()
                        eod_candidate = datetime.combine(check_in_time.date(), parsed_time)
                        # If configured checkout time is earlier than check-in, fall back to end-of-day
                        if eod_candidate < check_in_time:
                            eod_candidate = datetime.combine(check_in_time.date(), datetime.max.time()).replace(microsecond=0)
                        check_out_time = eod_candidate
                    except Exception:
                        check_out_time = datetime.combine(check_in_time.date(), datetime.max.time()).replace(microsecond=0)
                else:
                    check_out_time = datetime.combine(check_in_time.date(), datetime.max.time()).replace(microsecond=0)
            except Exception:
                check_out_time = datetime.now()

        # Calculate working hours (in hours)
        working_hours = (check_out_time - check_in_time).total_seconds() / 3600

        # Update the record
        cur.execute("""
            UPDATE attendance
            SET check_out_time = %s,
                working_hours = %s,
                status = 'check-out',
                timestamp = %s
            WHERE id = %s
        """, (check_out_time, working_hours, check_out_time, attendance_id))

        db.commit()

        # Send email notification if email is configured
        if record["email"] and current_app:
            try:
                email_service = EmailService(current_app)
                email_service.send_checkout_completion(
                    to_email=record["email"],
                    employee_name=record["full_name"],
                    date=check_out_time.strftime('%Y-%m-%d'),
                    check_in_time=check_in_time.strftime('%H:%M:%S'),
                    check_out_time=check_out_time.strftime('%H:%M:%S'),
                    working_hours=working_hours
                )
                logger.info(f"Sent check-out completion email to {record['email']}")
            except Exception as email_error:
                logger.error(f"Failed to send check-out completion email: {str(email_error)}")

        return jsonify({
            "status": "ok",
            "message": f"Check-out completed at {check_out_time.strftime('%H:%M:%S')}",
            "working_hours": round(working_hours, 2)
        })

    except Exception as e:
        db.rollback()
        logger.error(f"Error completing check-out for attendance ID {attendance_id}: {str(e)}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

    finally:
        cur.close()

