import os
import csv
import io
from datetime import datetime
from flask import render_template, request, jsonify, send_file, session, redirect, url_for, flash, current_app
from utils.db import get_connection, close_db
from blueprints.auth.utils import login_required
from . import bp
from werkzeug.utils import secure_filename
from PIL import Image

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


# Helper: programmatic admin check for JSON endpoints
def require_admin():
    if session.get("role") != "admin":
        return jsonify({
            "success": False,
            "error": "Admin access required"
        }), 403
    return None

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


# ------------------
# Validation helpers
# ------------------
ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp"}
ALLOWED_MIME = {"image/png", "image/jpeg", "image/webp"}


def _bad_request_with_audit(message):
    # Log validation/upload failure to audit_logs with minimal info
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_logs (user_id, action, module, details, ip_address)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            session.get("user_id"),
            "REJECT",
            "settings",
            message,
            request.remote_addr,
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        # Keep failure silent for audit logging, return original error to client
        pass

    return jsonify(success=False, error=message), 400


def _validate_time_hhmm(value):
    if not isinstance(value, str):
        return False
    parts = value.split(":")
    if len(parts) != 2:
        return False
    hh, mm = parts
    if not (hh.isdigit() and mm.isdigit()):
        return False
    h = int(hh)
    m = int(mm)
    return 0 <= h <= 23 and 0 <= m <= 59


def _validate_settings_payload(data):
    # Ensure dict
    if not isinstance(data, dict):
        return False, "Invalid JSON payload"

    # Reject unknown keys
    for k in data.keys():
        if k not in DEFAULTS:
            return False, f"Unknown setting key: {k}"

    # Per-key validation
    # recognition_threshold: float between 0.30 and 0.80
    if 'recognition_threshold' in data:
        try:
            v = float(data.get('recognition_threshold'))
        except Exception:
            return False, "recognition_threshold must be a float"
        if not (0.30 <= v <= 0.80):
            return False, "recognition_threshold out of allowed range (0.30-0.80)"

    # duplicate_interval: numeric minutes, 0 <= v <= 1440
    if 'duplicate_interval' in data:
        try:
            v = float(data.get('duplicate_interval'))
        except Exception:
            return False, "duplicate_interval must be a number"
        if v < 0 or v > 1440:
            return False, "duplicate_interval out of range (0-1440 minutes)"

    # snapshot_mode: enum
    if 'snapshot_mode' in data:
        v = str(data.get('snapshot_mode')).lower()
        if v not in ('on', 'off'):
            return False, "snapshot_mode must be 'on' or 'off'"

    # late_time: HH:MM
    if 'late_time' in data:
        if not _validate_time_hhmm(data.get('late_time')):
            return False, "late_time must be in HH:MM 24-hour format"

    # min_confidence: 0-100
    if 'min_confidence' in data:
        try:
            v = float(data.get('min_confidence'))
        except Exception:
            return False, "min_confidence must be a number"
        if v < 0 or v > 100:
            return False, "min_confidence must be between 0 and 100"

    # company_name: string <=255
    if 'company_name' in data:
        v = data.get('company_name')
        if v is None:
            return False, "company_name cannot be null"
        if not isinstance(v, str):
            return False, "company_name must be a string"
        if len(v) > 255:
            return False, "company_name too long"

    # company_logo: string path (optional)
    if 'company_logo' in data:
        v = data.get('company_logo')
        if v is None:
            return False, "company_logo cannot be null"
        if not isinstance(v, str):
            return False, "company_logo must be a string path"
        if len(v) > 1024:
            return False, "company_logo path too long"

    # camera_index: int 0-10
    if 'camera_index' in data:
        try:
            v = int(data.get('camera_index'))
        except Exception:
            return False, "camera_index must be an integer"
        if v < 0 or v > 10:
            return False, "camera_index out of allowed range (0-10)"

    # session_timeout: allowed values 15,30,60
    if 'session_timeout' in data:
        try:
            v = int(data.get('session_timeout'))
        except Exception:
            return False, "session_timeout must be an integer"
        if v not in (15, 30, 60):
            return False, "session_timeout must be one of 15, 30, 60"

    # login_alert: 'off' or a non-empty string (e.g., 'email')
    if 'login_alert' in data:
        v = data.get('login_alert')
        if not isinstance(v, str):
            return False, "login_alert must be a string"
        if v != 'off' and len(v.strip()) == 0:
            return False, "login_alert invalid"

    return True, None


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


def log_setting_change(cursor, user_id, key, old, new, ip):
    # Only log when value actually changed
    if str(old) == str(new):
        return

    cursor.execute("""
        INSERT INTO audit_logs (user_id, action, module, details, ip_address)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        user_id,
        "UPDATE",
        "settings",
        f"{key}: {old} → {new}",
        ip
    ))


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
    # admin-only guard for API saves
    admin_check = require_admin()
    if admin_check:
        return admin_check

    data = request.get_json()

    # Validate payload strictly (all-or-nothing)
    ok, err = _validate_settings_payload(data)
    if not ok:
        return _bad_request_with_audit(f"Settings validation failed: {err}")

    # Read current settings snapshot for auditing
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT setting_key, setting_value FROM settings")
    rows = cur.fetchall()
    old_settings = {k: v for k, v in rows}

    # Upsert incoming settings and write audit logs only for changed values
    for key, new_value in data.items():
        # Persist (insert or update) - keys are already validated
        cur.execute("""
            INSERT INTO settings (setting_key, setting_value)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
        """, (key, str(new_value)))

        # Audit log when changed
        try:
            log_setting_change(
                cursor=cur,
                user_id=session.get("user_id"),
                key=key,
                old=old_settings.get(key),
                new=new_value,
                ip=request.remote_addr
            )
        except Exception:
            # keep saving even if logging fails
            pass

    conn.commit()
    cur.close()
    conn.close()

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
    # admin-only guard for uploads
    admin_check = require_admin()
    if admin_check:
        return admin_check

    if "company_logo" not in request.files:
        return _bad_request_with_audit("File missing")

    file = request.files["company_logo"]
    if not file.filename:
        return _bad_request_with_audit("Empty filename")
    # Extension check
    secure_name = secure_filename(file.filename)
    if '.' not in secure_name:
        return _bad_request_with_audit("Invalid file extension")
    ext = secure_name.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXT:
        return _bad_request_with_audit("File type not allowed")

    # MIME type check
    mimetype = file.mimetype or ''
    if mimetype not in ALLOWED_MIME:
        return _bad_request_with_audit("MIME type not allowed")

    # Verify image content with Pillow
    try:
        file.stream.seek(0)
        img = Image.open(file.stream)
        img.verify()
    except Exception:
        return _bad_request_with_audit("Uploaded file is not a valid image")

    # Reset stream position and save using existing generated name
    file.stream.seek(0)
    filename = f"logo_{int(datetime.utcnow().timestamp())}.{ext}"
    full_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        file.save(full_path)
    except Exception:
        return _bad_request_with_audit("Failed to save uploaded file")

    web_path = f"/static/uploads/{filename}"
    try:
        save_setting("company_logo", web_path)
    except Exception:
        # Attempt to remove file if DB save fails
        try:
            os.remove(full_path)
        except Exception:
            pass
        return _bad_request_with_audit("Failed to persist company_logo setting")

    # Audit successful upload
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_logs (user_id, action, module, details, ip_address)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            session.get("user_id"),
            "UPLOAD",
            "settings",
            f"upload_logo success: {web_path}",
            request.remote_addr,
        ))
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass

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


# ---------------------------------------------------------
# CHANGE PASSWORD (Self-service for logged-in users)
# ---------------------------------------------------------
@bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """Allow any logged-in user to change their own password"""
    
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")
    
    if not all([old_password, new_password, confirm_password]):
        return jsonify({"success": False, "error": "All fields are required"}), 400
    
    if new_password != confirm_password:
        return jsonify({"success": False, "error": "New passwords do not match"}), 400
    
    # Validate new password strength
    from utils.validators import validate_password
    is_strong, msg = validate_password(new_password)
    if not is_strong:
        return jsonify({"success": False, "error": msg}), 400
    
    # Verify old password
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT password FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    
    if not user:
        cur.close()
        conn.close()
        return jsonify({"success": False, "error": "User not found"}), 404
    
    from blueprints.auth.utils import verify_password, hash_password
    if not verify_password(user["password"], old_password):
        cur.close()
        conn.close()
        
        # Audit failed attempt
        try:
            from db_utils import log_audit
            log_audit(user_id, 'PASSWORD_CHANGE_FAILED', 'settings', 'incorrect_old_password', request.remote_addr)
        except:
            pass
        
        return jsonify({"success": False, "error": "Current password is incorrect"}), 401
    
    # Update password
    hashed = hash_password(new_password)
    cur.execute("UPDATE users SET password = %s WHERE id = %s", (hashed, user_id))
    conn.commit()
    cur.close()
    conn.close()
    
    # Audit successful change
    try:
        from db_utils import log_audit
        log_audit(user_id, 'PASSWORD_CHANGED', 'settings', 'self_service', request.remote_addr)
    except:
        pass
    
    return jsonify({"success": True, "message": "Password changed successfully"})
