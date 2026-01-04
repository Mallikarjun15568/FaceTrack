from . import bp
from flask import render_template, session, redirect, url_for
from utils.db import get_db
from blueprints.auth.utils import login_required


# ================================
# ADMIN DASHBOARD (FINAL CLEAN)
# ================================
@bp.route("/")
@bp.route("/admin")
@bp.route("")
@bp.route("/dashboard")
@login_required
def admin_dashboard():
    role = session.get('role')

    # If user is not admin/hr, show employee dashboard
    if role not in ["admin", "hr"]:
        return render_template("dashboard_employee.html")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # 1) Total Employees
    cursor.execute("SELECT COUNT(*) AS total FROM employees")
    total_employees = cursor.fetchone()["total"]

    # 2) Total Departments
    cursor.execute("SELECT COUNT(*) AS total FROM departments")
    total_departments = cursor.fetchone()["total"]

    # 3) Present today
    cursor.execute("SELECT COUNT(*) AS present FROM attendance WHERE date = CURDATE()")
    today_present = cursor.fetchone()["present"]

    # 4) Recognition Today
    cursor.execute("""
        SELECT COUNT(*) AS logs 
        FROM recognition_logs 
        WHERE DATE(timestamp) = CURDATE()
    """)
    recognition_today = cursor.fetchone()["logs"]

    # 5) Recent Attendance (last 5)
    cursor.execute("""
        SELECT e.full_name, 
               DATE(a.check_in_time) AS date, 
               TIME(a.check_in_time) AS time,
               a.status
        FROM attendance a
        JOIN employees e ON e.id = a.employee_id
        WHERE a.check_in_time IS NOT NULL
        ORDER BY a.check_in_time DESC
        LIMIT 5
    """)
    recent_attendance = cursor.fetchall()

    # 6) Recent Recognitions (last 5)
    cursor.execute("""
        SELECT e.full_name, r.timestamp 
        FROM recognition_logs r
        JOIN employees e ON e.id = r.employee_id
        ORDER BY r.id DESC
        LIMIT 5
    """)
    recent_recognitions = cursor.fetchall()

    # 7) Weekly Attendance Chart Data
    cursor.execute("""
        SELECT DATE(date) AS day, COUNT(*) AS count
        FROM attendance
        WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(date)
    """)
    weekly_rows = cursor.fetchall()

    weekly_data = {
        "labels": [str(row["day"]) for row in weekly_rows],
        "data": [row["count"] for row in weekly_rows]
    }

    # 8) Department Employee Distribution
    cursor.execute("""
        SELECT d.name AS department, COUNT(e.id) AS total
        FROM departments d
        LEFT JOIN employees e ON e.department_id = d.id
        GROUP BY d.id
    """)
    dept_rows = cursor.fetchall()

    department_data = {
        "labels": [row["department"] for row in dept_rows],
        "data": [row["total"] for row in dept_rows]
    }

    return render_template(
        "dashboard_admin.html",
        total_employees=total_employees,
        total_departments=total_departments,
        today_present=today_present,
        recognition_today=recognition_today,
        recent_attendance=recent_attendance,
        recent_recognitions=recent_recognitions,
        weekly_data=weekly_data,
        department_data=department_data
    )
