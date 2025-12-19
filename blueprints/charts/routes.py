# ============================================
# FaceTrack Pro - Charts Blueprint
# Phase 1 (Charts) + Phase 2 (Live Stats)
# ============================================

from flask import jsonify, request, session
from datetime import datetime, date
from functools import wraps
from utils.db import get_db
from . import bp   # IMPORT BLUEPRINT


# ==========================================
# DECORATOR: Require Login
# ==========================================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper


# ==========================================
# 1. DASHBOARD STATS (PHASE 1)
# ==========================================
@bp.route("/dashboard-stats", methods=["GET"])
@login_required
def dashboard_stats():
    db = get_db()
    cur = db.cursor(dictionary=True)
    today = date.today()

    # Total active employees
    cur.execute("""
        SELECT COUNT(*) AS total
        FROM employees
        WHERE status = 'Active'
    """)
    total_employees = cur.fetchone()["total"]

    # Present (checked in today)
    cur.execute("""
        SELECT COUNT(*) AS present
        FROM attendance
        WHERE date = %s AND check_in_time IS NOT NULL
    """, (today,))
    present = cur.fetchone()["present"]

    # Late (example rule: after 10:15)
    cur.execute("""
        SELECT COUNT(*) AS late
        FROM attendance
        WHERE date = %s AND check_in_time > '10:15:00'
    """, (today,))
    late = cur.fetchone()["late"]

    # On Leave
    cur.execute("""
        SELECT COUNT(*) AS on_leave
        FROM leaves
        WHERE %s BETWEEN start_date AND end_date
          AND status = 'Approved'
    """, (today,))
    on_leave = cur.fetchone()["on_leave"]

    absent = total_employees - present - on_leave

    # Department-wise present count
    cur.execute("""
        SELECT d.name AS department, COUNT(a.id) AS present
        FROM departments d
        LEFT JOIN employees e ON e.department_id = d.id
        LEFT JOIN attendance a
            ON a.employee_id = e.id AND a.date = %s
        GROUP BY d.id, d.name
    """, (today,))
    departments = cur.fetchall()

    # Working hours distribution
    cur.execute("""
        SELECT
            SUM(working_hours < 4) AS lt4,
            SUM(working_hours BETWEEN 4 AND 6) AS b46,
            SUM(working_hours BETWEEN 6 AND 8) AS b68,
            SUM(working_hours > 8) AS gt8
        FROM attendance
        WHERE date = %s AND working_hours IS NOT NULL
    """, (today,))
    wh = cur.fetchone()

    cur.close()

    return jsonify({
        "success": True,
        "today": {
            "present": present,
            "absent": absent,
            "late": late,
            "onLeave": on_leave
        },
        "departments": departments,
        "workingHours": {
            "lessThan4": wh["lt4"] or 0,
            "between4And6": wh["b46"] or 0,
            "between6And8": wh["b68"] or 0,
            "moreThan8": wh["gt8"] or 0
        }
    })


# ==========================================
# 2. REPORT STATS (PHASE 1)
# ==========================================
@bp.route("/report-stats", methods=["POST"])
@login_required
def report_stats():
    data = request.json
    start_date = data.get("startDate")
    end_date = data.get("endDate")

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Weekly trend (based on selected range)
    cur.execute("""
        SELECT DATE(date) AS day, COUNT(*) AS present
        FROM attendance
        WHERE date BETWEEN %s AND %s
          AND check_in_time IS NOT NULL
        GROUP BY DATE(date)
        ORDER BY DATE(date)
    """, (start_date, end_date))
    weekly = cur.fetchall()

    # Monthly attendance rate
    cur.execute("""
        SELECT
            DATE_FORMAT(date, '%b') AS month,
            COUNT(check_in_time) * 100.0 / COUNT(*) AS rate
        FROM attendance
        WHERE date BETWEEN %s AND %s
        GROUP BY YEAR(date), MONTH(date)
        ORDER BY YEAR(date), MONTH(date)
    """, (start_date, end_date))
    monthly = cur.fetchall()

    # Employee performance (last 30 days)
    cur.execute("""
        SELECT e.name,
               COUNT(a.check_in_time) * 100.0 / COUNT(*) AS rate
        FROM employees e
        JOIN attendance a ON a.employee_id = e.id
        WHERE a.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY e.id, e.name
        ORDER BY rate DESC
        LIMIT 10
    """)
    employees = cur.fetchall()

    cur.close()

    return jsonify({
        "success": True,
        "weekly": {
            "labels": [r["day"].strftime("%a") for r in weekly],
            "present": [r["present"] for r in weekly]
        },
        "monthly": {
            "months": [r["month"] for r in monthly],
            "attendanceRate": [float(r["rate"]) for r in monthly]
        },
        "employees": employees
    })


# ==========================================
# 3. LIVE STATS (PHASE 2)
# ==========================================
@bp.route("/live-stats", methods=["GET"])
@login_required
def live_stats():
    db = get_db()
    cur = db.cursor(dictionary=True)
    today = date.today()

    cur.execute("""
        SELECT
            COUNT(check_in_time) AS present,
            SUM(check_in_time > '10:15:00') AS late
        FROM attendance
        WHERE date = %s
    """, (today,))
    stats = cur.fetchone()

    cur.close()

    return jsonify({
        "success": True,
        "present": stats["present"] or 0,
        "late": stats["late"] or 0,
        "timestamp": datetime.now().isoformat()
    })


# ==========================================
# 4. RECENT ATTENDANCE (PHASE 2)
# ==========================================
@bp.route("/recent-attendance", methods=["GET"])
@login_required
def recent_attendance():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT e.name,
               a.check_in_time,
               a.check_out_time,
               a.captured_photo_path
        FROM attendance a
        JOIN employees e ON e.id = a.employee_id
        WHERE a.date = CURDATE()
        ORDER BY a.updated_at DESC
        LIMIT 10
    """)

    rows = cur.fetchall()
    cur.close()

    return jsonify({
        "success": True,
        "records": rows
    })
