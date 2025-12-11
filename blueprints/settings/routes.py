import os
import csv
import io
from datetime import datetime
from flask import render_template, request, jsonify, send_file, session, redirect, url_for, flash
from utils.db import get_connection, close_db
from blueprints.auth.utils import login_required
from . import bp

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DEFAULT SETTINGS
DEFAULTS = {
    "recognition_threshold": "0.42",
    "duplicate_interval": "5",
    "snapshot_mode": "off",
    "late_time": "09:30",
    "min_confidence": "85",
    "company_name": "",
    "company_logo": "/static/uploads/logo.png",
    "camera_index": "0",
    "session_timeout": "30",
    "login_alert": "off"
}

# ---------------------------------------------------------
# Admin-only protection
# ---------------------------------------------------------
@bp.before_request
@login_required
def restrict_to_admin():
    if session.get("role") != "admin":
        flash("Only admins can access Settings", "error")
        return redirect(url_for("dashboard.admin_dashboard"))


# ---------------------------------------------------------
# Load all settings from DB → return dict
# ---------------------------------------------------------
def load_settings():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT setting_key, setting_value FROM settings")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    out = {}
    for k, v in rows:
        out[k] = v
    return out


# ---------------------------------------------------------
# Save/update a single setting
# ---------------------------------------------------------
def save_setting(key, value):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO settings (setting_key, setting_value)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
    """, (key, str(value)))

    conn.commit()
    cur.close()
    conn.close()


# ---------------------------------------------------------
# Render Settings Page (Jinja Prefilled)
# ---------------------------------------------------------
@bp.route("/")
def settings_page():
    saved = load_settings()
    merged = {k: saved.get(k, DEFAULTS[k]) for k in DEFAULTS.keys()}
    return render_template("settings.html", settings=merged)


# ---------------------------------------------------------
# Save All Settings (POST)
# ---------------------------------------------------------
@bp.route("/api", methods=["POST"])
def settings_api():
    data = request.get_json()

    for key in DEFAULTS.keys():
        if key in data:
            save_setting(key, data[key])

    return jsonify(success=True)


# ---------------------------------------------------------
# Upload Company Logo
# ---------------------------------------------------------
@bp.route("/upload-logo", methods=["POST"])
def upload_logo():
    if "company_logo" not in request.files:
        return jsonify(success=False, error="File missing")

    file = request.files["company_logo"]
    if not file.filename:
        return jsonify(success=False, error="Empty filename")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"logo_{int(datetime.utcnow().timestamp())}.{ext}"

    full_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(full_path)

    web_path = f"/static/uploads/{filename}"
    save_setting("company_logo", web_path)

    return jsonify(success=True, path=web_path)


# ---------------------------------------------------------
# Export Attendance CSV
# ---------------------------------------------------------
@bp.route("/export/attendance")
def export_attendance():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM attendance")
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]

    cur.close()
    conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(cols)
    writer.writerows(rows)
    buf.seek(0)

    return send_file(
        io.BytesIO(buf.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="attendance.csv"
    )


# ---------------------------------------------------------
# Export Employees CSV
# ---------------------------------------------------------
@bp.route("/export/employees")
def export_employees():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM employees")
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]

    cur.close()
    conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(cols)
    writer.writerows(rows)
    buf.seek(0)

    return send_file(
        io.BytesIO(buf.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="employees.csv"
    )
