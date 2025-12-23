import os
import csv
import io
from datetime import datetime
from flask import render_template, request, jsonify, send_file, session, redirect, url_for, flash, current_app
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

    # --- Apply immediate runtime config updates for important keys ---
    try:
        # Recognition threshold -> EMBED_THRESHOLD (float)
        if 'recognition_threshold' in data:
            try:
                current_app.config['EMBED_THRESHOLD'] = float(data.get('recognition_threshold'))
            except Exception:
                pass

        # Duplicate Attendance Interval (minutes) -> KIOSK_COOLDOWN_SECONDS (seconds)
        if 'duplicate_interval' in data:
            try:
                mins = float(data.get('duplicate_interval'))
                # if invalid or zero, keep existing
                if mins >= 0:
                    current_app.config['KIOSK_COOLDOWN_SECONDS'] = mins * 60.0
            except Exception:
                pass

        # Snapshot mode -> SAVE_SNAPSHOTS (boolean override)
        if 'snapshot_mode' in data:
            current_app.config['SAVE_SNAPSHOTS'] = (str(data.get('snapshot_mode')).lower() == 'on')

        # Minimum confidence (store for runtime checks)
        if 'min_confidence' in data:
            try:
                current_app.config['MIN_CONFIDENCE'] = float(data.get('min_confidence'))
            except Exception:
                pass

        # Camera index (runtime default)
        if 'camera_index' in data:
            try:
                current_app.config['DEFAULT_CAMERA_INDEX'] = int(data.get('camera_index'))
            except Exception:
                pass

        # Session timeout -> PERMANENT_SESSION_LIFETIME (seconds)
        if 'session_timeout' in data:
            try:
                st_min = int(data.get('session_timeout'))
                current_app.config['PERMANENT_SESSION_LIFETIME'] = st_min * 60
            except Exception:
                pass

        # Misc: login_alert, company_name, company_logo, late_time saved already; optionally mirror to config
        if 'login_alert' in data:
            current_app.config['LOGIN_ALERT'] = data.get('login_alert')
        if 'company_name' in data:
            current_app.config['COMPANY_NAME'] = data.get('company_name')
        if 'company_logo' in data:
            current_app.config['COMPANY_LOGO'] = data.get('company_logo')
        if 'late_time' in data:
            current_app.config['LATE_TIME'] = data.get('late_time')
    except Exception:
        # don't fail saving if runtime sync has a problem
        pass

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
