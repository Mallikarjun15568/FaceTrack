from . import bp
from flask import jsonify, request, render_template, session, redirect, flash
from utils.db import get_db
from datetime import datetime, date, time, timedelta
from blueprints.auth.utils import login_required


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
def reports_page():
    # Only admin and HR can view reports
    if session.get("role") not in ["admin", "hr"]:
        flash("Only admins and HR can view reports", "error")
        return redirect("/dashboard")
    return render_template("reports.html")


# SUMMARY API (FIXED attendance%)
@bp.route("/api/summary")
def api_summary():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT COUNT(*) AS total FROM employees")
    total = cur.fetchone()["total"] or 0

    cur.execute("SELECT COUNT(*) AS present FROM attendance WHERE date = CURDATE() AND status='present'")
    present = cur.fetchone()["present"] or 0

    cur.execute("SELECT COUNT(*) AS late FROM attendance WHERE date = CURDATE() AND status='late'")
    late = cur.fetchone()["late"] or 0

    cur.execute("SELECT COUNT(*) AS absent FROM attendance WHERE date = CURDATE() AND status='absent'")
    absent = cur.fetchone()["absent"] or 0

    cur.close()

    # FIX — attendance % calculation
    percent = 0
    if total > 0:
        percent = round((present / total) * 100)

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
def api_departments():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT id, name FROM departments ORDER BY name ASC")
    rows = cur.fetchall()
    cur.close()

    return jsonify({"status": "ok", "departments": rows})


# EMPLOYEES
@bp.route("/api/employees")
def api_employees():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT id, full_name FROM employees ORDER BY full_name ASC")
    rows = cur.fetchall()
    cur.close()

    return jsonify({"status": "ok", "employees": rows})


# TABLE API
@bp.route("/api/table")
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
            a.date,
            a.entry_time,
            a.exit_time,
            a.status,
            (SELECT image_path FROM recognition_logs
             WHERE employee_id = a.employee_id
               AND DATE(timestamp) = a.date
             ORDER BY id DESC LIMIT 1) AS snapshot,
            TIMEDIFF(a.exit_time, a.entry_time) AS work_hours
        FROM attendance a
        LEFT JOIN employees e ON e.id = a.employee_id
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE 1=1
    """

    params = []

    if from_date:
        query += " AND a.date >= %s"
        params.append(from_date)

    if to_date:
        query += " AND a.date <= %s"
        params.append(to_date)

    if employee:
        query += " AND e.full_name = %s"
        params.append(employee)

    if dept:
        query += " AND d.name = %s"
        params.append(dept)

    query += " ORDER BY a.date DESC, a.entry_time ASC"

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


# CHART API (FULL FIXED)
@bp.route("/api/chart-data")
def api_chart_data():
    db = get_db()
    cur = db.cursor(dictionary=True)

    # DAILY ATTENDANCE
    cur.execute("""
        SELECT date,
               SUM(CASE WHEN status='present' THEN 1 ELSE 0 END) AS present,
               SUM(CASE WHEN status='late' THEN 1 ELSE 0 END) AS late,
               SUM(CASE WHEN status='absent' THEN 1 ELSE 0 END) AS absent
        FROM attendance
        WHERE date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        GROUP BY date
        ORDER BY date ASC
    """)
    daily = cur.fetchall()

    # DEPARTMENT WISE
    cur.execute("""
        SELECT d.name AS department,
               COUNT(a.id) AS present
        FROM attendance a
        LEFT JOIN employees e ON e.id = a.employee_id
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE a.date = CURDATE() AND a.status='present'
        GROUP BY d.name
    """)
    departments = cur.fetchall()

    cur.close()

    return jsonify({
        "status": "ok",
        "chart": {
            "daily": jsonify_safe(daily),
            "departments": jsonify_safe(departments)
        }
    })


# CSV EXPORT
@bp.route("/api/export/csv")
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
            a.date,
            a.entry_time,
            a.exit_time,
            a.status,
            TIMEDIFF(a.exit_time, a.entry_time) AS work_hours
        FROM attendance a
        LEFT JOIN employees e ON e.id = a.employee_id
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE 1=1
    """

    params = []

    if from_date:
        query += " AND a.date >= %s"
        params.append(from_date)

    if to_date:
        query += " AND a.date <= %s"
        params.append(to_date)

    if employee:
        query += " AND e.full_name = %s"
        params.append(employee)

    if dept:
        query += " AND d.name = %s"
        params.append(dept)

    query += " ORDER BY a.date DESC, a.entry_time ASC"

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


# PDF EXPORT
@bp.route("/api/export/pdf")
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
            a.date,
            a.entry_time,
            a.exit_time,
            a.status,
            TIMEDIFF(a.exit_time, a.entry_time) AS work_hours
        FROM attendance a
        LEFT JOIN employees e ON e.id = a.employee_id
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE 1=1
    """

    params = []

    if from_date:
        query += " AND a.date >= %s"
        params.append(from_date)

    if to_date:
        query += " AND a.date <= %s"
        params.append(to_date)

    if employee:
        query += " AND e.full_name = %s"
        params.append(employee)

    if dept:
        query += " AND d.name = %s"
        params.append(dept)

    query += " ORDER BY a.date DESC, a.entry_time ASC"

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
