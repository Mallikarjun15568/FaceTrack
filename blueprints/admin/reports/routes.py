from . import bp
from flask import jsonify, request, render_template, session, redirect, flash
from utils.db import get_db
from datetime import datetime, date, time, timedelta
from blueprints.auth.utils import login_required, role_required

# ==================================================================================
# REPORTS BLUEPRINT - ALL QUERIES USE DATE(check_in_time)
# ==================================================================================
# IMPORTANT: All reports APIs use DATE(check_in_time) to derive attendance dates.
# Legacy 'date' column in attendance table is IGNORED.
# 
# Filtering Rules:
# - WHERE check_in_time IS NOT NULL (excludes legacy/corrupted rows)
# - ORDER BY check_in_time DESC (chronological order)
# 
# This ensures clean, consistent reporting across all endpoints.
# ==================================================================================


# SAFE JSON FIX
def jsonify_safe(rows):
    for r in rows:
        for k, v in list(r.items()):
            if isinstance(v, (datetime, date, time, timedelta)):
                r[k] = str(v)
            if isinstance(v, (bytes, bytearray)):
                try:
                    r[k] = v.decode("utf-8")
                except:
                    r[k] = str(v)
    return rows


# PAGE
@bp.route("/")
@login_required
@role_required("admin", "hr")
def reports_page():
    return render_template("reports.html", employee_view=False)


# SUMMARY API (Today's attendance counts)
# Uses DATE(check_in_time) = CURDATE() for filtering
# SUMMARY API (Today's attendance counts)
# Uses DATE(check_in_time) = CURDATE() for filtering
@bp.route("/api/summary")
@login_required
@role_required("admin", "hr")
def api_summary():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS total FROM employees")
    total = cur.fetchone()["total"] or 0

    # Today's attendance
    today = date.today()
    cur.execute("SELECT COUNT(DISTINCT employee_id) AS present FROM attendance WHERE DATE(check_in_time) = %s AND check_in_time IS NOT NULL", (today,))
    present = cur.fetchone()["present"] or 0

    # Late entries today (after 9:30 AM)
    cur.execute("SELECT COUNT(DISTINCT employee_id) AS late FROM attendance WHERE DATE(check_in_time) = %s AND check_in_time IS NOT NULL AND TIME(check_in_time) > '09:30:00'", (today,))
    late = cur.fetchone()["late"] or 0

    # Absent: total - (present + late) but only count employees who should be present today
    # For simplicity, absent = total - present (since late are included in present)
    absent = max(0, total - present)

    cur.close()

    # Attendance percentage for today
    percent = 0
    if total > 0:
        percent = round((present / total) * 100) if total > 0 else 0

    return jsonify({
        "status": "ok",
        "summary": {
            "total": total,
            "present": present,
            "late": late,
            "absent": absent,
            "attendance_percent": percent
        }
    })


# DEPARTMENTS
@bp.route("/api/departments")
@login_required
@role_required("admin", "hr")
def api_departments():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT id, name FROM departments ORDER BY name ASC")
    rows = cur.fetchall()
    cur.close()

    return jsonify({"status": "ok", "departments": rows})


# EMPLOYEES
@bp.route("/api/employees")
@login_required
@role_required("admin", "hr")
def api_employees():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT id, full_name FROM employees ORDER BY full_name ASC")
    rows = cur.fetchall()
    cur.close()

    return jsonify({"status": "ok", "employees": rows})


# TABLE API - Detailed Attendance Records
# Returns all attendance records with DATE(check_in_time) derived dates
# Excludes legacy rows where check_in_time IS NULL
@bp.route("/api/table")
@login_required
@role_required("admin", "hr")
def api_table():
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    employee = request.args.get("employee")
    dept = request.args.get("department")

    db = get_db()
    cur = db.cursor(dictionary=True)

    query = """
        SELECT 
            a.id,
            e.full_name AS name,
            d.name AS department,
            DATE(a.check_in_time) AS date,
            a.check_in_time AS entry_time,
            a.check_out_time AS exit_time,
            a.status,
            (SELECT image_path FROM recognition_logs
             WHERE employee_id = a.employee_id
               AND DATE(timestamp) = DATE(a.check_in_time)
             ORDER BY id DESC LIMIT 1) AS snapshot,
            a.working_hours AS work_hours
        FROM attendance a
        LEFT JOIN employees e ON e.id = a.employee_id
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE a.check_in_time IS NOT NULL
    """

    params = []
    
    # If employee role, automatically filter by their own ID
    if session.get("role") == "employee" and session.get("employee_id"):
        query += " AND a.employee_id = %s"
        params.append(session.get("employee_id"))

    if from_date:
        query += " AND DATE(a.check_in_time) >= %s"
        params.append(from_date)

    if to_date:
        query += " AND DATE(a.check_in_time) <= %s"
        params.append(to_date)

    if employee:
        query += " AND e.full_name = %s"
        params.append(employee)

    if dept:
        query += " AND d.name = %s"
        params.append(dept)

    query += " ORDER BY a.check_in_time DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()

    # Normalize path
    for r in rows:
        snap = r.get("snapshot")
        if snap:
            if not snap.startswith("/"):
                if "static/" in snap:
                    r["snapshot"] = "/" + snap[snap.find("static/"):]
                else:
                    r["snapshot"] = "/static/" + snap

    return jsonify({"status": "ok", "records": jsonify_safe(rows)})


# CHART API - Daily & Department-wise attendance trends
# Uses DATE(check_in_time) for date aggregation
@bp.route("/api/chart-data")
@login_required
@role_required("admin", "hr")
def api_chart_data():
    db = get_db()
    cur = db.cursor(dictionary=True)

    # Get date range (last 7 days)
    cur.execute("SELECT DATE_SUB(CURDATE(), INTERVAL 6 DAY) as start_date, CURDATE() as end_date")
    date_range = cur.fetchone()
    start_date = date_range['start_date']
    end_date = date_range['end_date']

    # Get total employees
    cur.execute("SELECT COUNT(*) AS total FROM employees")
    total_employees = cur.fetchone()["total"] or 0

    # Get attendance summary for the period
    cur.execute("""
        SELECT
            COUNT(DISTINCT CASE WHEN present_days > 0 AND late_days = 0 THEN employee_id END) as present_on_time,
            COUNT(DISTINCT CASE WHEN late_days > 0 THEN employee_id END) as present_late,
            COUNT(DISTINCT CASE WHEN present_days = 0 THEN employee_id END) as absent
        FROM (
            SELECT
                e.id as employee_id,
                COUNT(DISTINCT DATE(a.check_in_time)) as present_days,
                COUNT(DISTINCT CASE WHEN TIME(a.check_in_time) > '09:30:00' THEN DATE(a.check_in_time) END) as late_days
            FROM employees e
            LEFT JOIN attendance a ON e.id = a.employee_id
                AND DATE(a.check_in_time) BETWEEN %s AND %s
                AND a.check_in_time IS NOT NULL
            GROUP BY e.id
        ) attendance_summary
    """, (start_date, end_date))

    summary = cur.fetchone()

    # DAILY ATTENDANCE (keep existing logic for line chart)
    cur.execute("""
        SELECT DATE(check_in_time) AS date,
               COUNT(DISTINCT employee_id) AS present,
               COUNT(DISTINCT CASE WHEN TIME(check_in_time) > '09:30:00' THEN employee_id END) AS late,
               0 AS absent  -- Will calculate below
        FROM attendance
        WHERE check_in_time IS NOT NULL
          AND DATE(check_in_time) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY DATE(check_in_time)
        ORDER BY DATE(check_in_time) ASC
    """)
    daily = cur.fetchall()

    # Calculate absent for each day (fix: absent = total - (present + late))
    for d in daily:
        total_present_today = d["present"] + d["late"]
        d["absent"] = max(0, total_employees - total_present_today)

    # DEPARTMENT WISE - Show all departments with weekly attendance percentage
    cur.execute("""
        SELECT d.name AS department,
               ROUND(
                   (COUNT(a.employee_id) / (COUNT(DISTINCT e.id) * 7)) * 100, 1
               ) AS attendance_percentage
        FROM departments d
        LEFT JOIN employees e ON e.department_id = d.id
        LEFT JOIN attendance a ON a.employee_id = e.id AND DATE(a.check_in_time) BETWEEN %s AND %s
        GROUP BY d.id, d.name
        ORDER BY attendance_percentage DESC, d.name ASC
    """, (start_date, end_date))
    departments = cur.fetchall()

    cur.close()

    return jsonify({
        "status": "ok",
        "chart": {
            "daily": jsonify_safe(daily),
            "departments": jsonify_safe(departments),
            "summary": {
                "present": summary['present_on_time'] if summary else 0,
                "late": summary['present_late'] if summary else 2,
                "absent": summary['absent'] if summary else 7
            }
        }
    })


# CSV EXPORT - Export attendance records to CSV
# Uses DATE(check_in_time) for date column, excludes NULL check_in_time rows
@bp.route("/api/export/csv")
@login_required
@role_required("admin", "hr")
def export_csv():
    from flask import Response
    import csv
    from io import StringIO

    from_date = request.args.get("from")
    to_date = request.args.get("to")
    employee = request.args.get("user")
    dept = request.args.get("department")

    db = get_db()
    cur = db.cursor(dictionary=True)

    query = """
        SELECT 
            e.full_name AS name,
            d.name AS department,
            DATE(a.check_in_time) AS date,
            a.check_in_time AS entry_time,
            a.check_out_time AS exit_time,
            a.status,
            a.working_hours AS work_hours
        FROM attendance a
        LEFT JOIN employees e ON e.id = a.employee_id
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE a.check_in_time IS NOT NULL
    """

    params = []

    if from_date:
        query += " AND DATE(a.check_in_time) >= %s"
        params.append(from_date)

    if to_date:
        query += " AND DATE(a.check_in_time) <= %s"
        params.append(to_date)

    if employee:
        query += " AND e.full_name = %s"
        params.append(employee)

    if dept:
        query += " AND d.name = %s"
        params.append(dept)

    query += " ORDER BY a.check_in_time DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()

    # Create CSV
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Date", "Employee", "Department", "Status", "Entry Time", "Exit Time", "Work Hours"])

    # Data
    for row in rows:
        writer.writerow([
            row.get("date", ""),
            row.get("name", ""),
            row.get("department", ""),
            row.get("status", ""),
            row.get("entry_time", ""),
            row.get("exit_time", ""),
            str(row.get("work_hours", ""))
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=attendance_report_{date.today()}.csv"}
    )


# PDF EXPORT - Export attendance records to PDF
# Uses DATE(check_in_time) for date column, excludes NULL check_in_time rows
@bp.route("/api/export/pdf")
@login_required
@role_required("admin", "hr")
def export_pdf():
    from flask import make_response
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from io import BytesIO

    from_date = request.args.get("from")
    to_date = request.args.get("to")
    employee = request.args.get("user")
    dept = request.args.get("department")

    db = get_db()
    cur = db.cursor(dictionary=True)

    query = """
        SELECT 
            e.full_name AS name,
            d.name AS department,
            DATE(a.check_in_time) AS date,
            a.check_in_time AS entry_time,
            a.check_out_time AS exit_time,
            a.status,
            a.working_hours AS work_hours
        FROM attendance a
        LEFT JOIN employees e ON e.id = a.employee_id
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE a.check_in_time IS NOT NULL
    """

    params = []

    if from_date:
        query += " AND DATE(a.check_in_time) >= %s"
        params.append(from_date)

    if to_date:
        query += " AND DATE(a.check_in_time) <= %s"
        params.append(to_date)

    if employee:
        query += " AND e.full_name = %s"
        params.append(employee)

    if dept:
        query += " AND d.name = %s"
        params.append(dept)

    query += " ORDER BY a.check_in_time DESC"

    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []

    styles = getSampleStyleSheet()

    # Title
    title = Paragraph("<b>Attendance Report</b>", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 20))

    # Table data
    data = [["Date", "Employee", "Department", "Status", "Entry", "Exit", "Hours"]]

    for row in rows:
        data.append([
            str(row.get("date", "")),
            str(row.get("name", "")),
            str(row.get("department", "")),
            str(row.get("status", "")),
            str(row.get("entry_time", "")),
            str(row.get("exit_time", "")),
            str(row.get("work_hours", ""))
        ])

    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=attendance_report_{date.today()}.pdf"

    return response
