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
            ) AS snapshot
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

    return jsonify({"status": "ok", "records": rows})
