import os
import csv
import io
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, send_file, session, redirect, url_for, flash, current_app
from utils.db import get_connection, close_db
from blueprints.auth.utils import login_required, role_required
from . import bp
from werkzeug.utils import secure_filename
from PIL import Image
import cv2

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global cache for camera detection
_camera_cache = None
_camera_cache_timestamp = None
CAMERA_CACHE_TTL = 300  # 5 minutes

# DEFAULT SETTINGS
DEFAULTS = {
    "recognition_threshold": "0.42",
    "duplicate_interval": "5",
    "snapshot_mode": "off",
    "late_time": "09:30",
    "checkout_time": "18:00",
    "min_confidence": "85",
    "company_name": "",
    "company_logo": "/static/images/FaceTrack_logo.png",
    "camera_device": "0",
    "session_timeout": "30",
    "login_alerts": "off",
    "exit_pin": ""
}


# Helper: programmatic admin check for JSON endpoints
def require_admin():
    if session.get("role") != "admin":
        return jsonify({
            "success": False,
            "error": "Admin access required"
        }), 403
    return None


# Helper: detect available camera devices (with caching)
def detect_cameras():
    """Detect available camera devices on the system (cached for 5 minutes)"""
    global _camera_cache, _camera_cache_timestamp
    
    # Check if we have valid cached data
    now = datetime.now()
    if (_camera_cache is not None and _camera_cache_timestamp is not None and 
        now - _camera_cache_timestamp < timedelta(seconds=CAMERA_CACHE_TTL)):
        return _camera_cache
    
    # Detect cameras (quick check without reading frames)
    cameras = []
    for i in range(10):  # Check first 10 camera indices
        try:
            # Quick check: just try to open camera without reading frames
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            available = cap.isOpened()
            
            if available:
                # Get basic camera info without reading frames
                camera_name = f"Camera {i}"
                try:
                    # Try to get camera properties (this is usually fast)
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    if width > 0 and height > 0:
                        camera_name = f"Camera {i} ({width}x{height})"
                except:
                    pass
                
                cameras.append({
                    "index": i,
                    "name": camera_name,
                    "available": True
                })
            else:
                cameras.append({
                    "index": i,
                    "name": f"Camera {i}",
                    "available": False
                })
            
            # Always release the camera immediately
            cap.release()
            
        except Exception as e:
            cameras.append({
                "index": i,
                "name": f"Camera {i}",
                "available": False
            })
    
    # Cache the results
    _camera_cache = cameras
    _camera_cache_timestamp = now
    
    return cameras


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
        return False, "Invalid payload"

    # Filter out CSRF token and other non-setting keys
    settings_data = {k: v for k, v in data.items() if k != 'csrf_token'}

    # Reject unknown keys
    for k in settings_data.keys():
        if k not in DEFAULTS:
            return False, f"Unknown setting key: {k}"

    # Per-key validation
    # recognition_threshold: float between 0.30 and 0.80
    if 'recognition_threshold' in settings_data:
        try:
            v = float(settings_data.get('recognition_threshold'))
        except Exception:
            return False, "recognition_threshold must be a float"
        if not (0.30 <= v <= 0.80):
            return False, "recognition_threshold out of allowed range (0.30-0.80)"

    # duplicate_interval: numeric minutes, 0 <= v <= 1440
    if 'duplicate_interval' in settings_data:
        try:
            v = float(settings_data.get('duplicate_interval'))
        except Exception:
            return False, "duplicate_interval must be a number"
        if v < 0 or v > 1440:
            return False, "duplicate_interval out of range (0-1440 minutes)"

    # snapshot_mode: enum
    if 'snapshot_mode' in settings_data:
        v = str(settings_data.get('snapshot_mode')).lower()
        if v not in ('on', 'off'):
            return False, "snapshot_mode must be 'on' or 'off'"

    # late_time: HH:MM
    if 'late_time' in settings_data:
        if not _validate_time_hhmm(settings_data.get('late_time')):
            return False, "late_time must be in HH:MM 24-hour format"

    # min_confidence: 0-100
    if 'min_confidence' in settings_data:
        try:
            v = float(settings_data.get('min_confidence'))
        except Exception:
            return False, "min_confidence must be a number"
        if v < 0 or v > 100:
            return False, "min_confidence must be between 0 and 100"

    # company_name: string <=255
    if 'company_name' in settings_data:
        v = settings_data.get('company_name')
        if v is None:
            return False, "company_name cannot be null"
        if not isinstance(v, str):
            return False, "company_name must be a string"
        if len(v) > 255:
            return False, "company_name too long"

    # company_logo: string path (optional)
    if 'company_logo' in settings_data:
        v = settings_data.get('company_logo')
        if v is None:
            return False, "company_logo cannot be null"
        if not isinstance(v, str):
            return False, "company_logo must be a string path"
        if len(v) > 1024:
            return False, "company_logo path too long"

    # camera_device: int 0-10
    if 'camera_device' in settings_data:
        try:
            v = int(settings_data.get('camera_device'))
        except Exception:
            return False, "camera_device must be an integer"
        if v < 0 or v > 10:
            return False, "camera_device out of allowed range (0-10)"

    # session_timeout: int 5-480
    if 'session_timeout' in settings_data:
        try:
            v = int(settings_data.get('session_timeout'))
        except Exception:
            return False, "session_timeout must be an integer"
        if v < 5 or v > 480:
            return False, "session_timeout out of allowed range (5-480 minutes)"

    # login_alerts: 'on' or 'off'
    if 'login_alerts' in settings_data:
        v = str(settings_data.get('login_alerts')).lower()
        if v not in ('on', 'off'):
            return False, "login_alerts must be 'on' or 'off'"

    # exit_pin: empty string or 4 digits
    if 'exit_pin' in settings_data:
        v = settings_data.get('exit_pin')
        if v is None:
            return False, "exit_pin cannot be null"
        if not isinstance(v, str):
            return False, "exit_pin must be a string"
        if v != "" and (len(v) != 4 or not v.isdigit()):
            return False, "exit_pin must be empty or exactly 4 digits"

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
    
    # Detect available cameras (cached, won't trigger camera every time)
    available_cameras = detect_cameras()
    
    return render_template("settings.html", settings=merged, available_cameras=available_cameras)


# API endpoint to refresh camera detection
# ---------------------------------------------------------
@bp.route("/api/detect-cameras")
def detect_cameras_api():
    """API endpoint to manually refresh camera detection"""
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    try:
        # Force refresh by clearing cache
        global _camera_cache, _camera_cache_timestamp
        _camera_cache = None
        _camera_cache_timestamp = None
        
        cameras = detect_cameras()
        return jsonify({
            "success": True,
            "cameras": cameras,
            "message": f"Detected {len([c for c in cameras if c['available']])} available cameras"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ---------------------------------------------------------
# Save All Settings (POST)
# ---------------------------------------------------------
@bp.route("/api", methods=["POST"])
def settings_api():
    # admin-only guard for API saves
    admin_check = require_admin()
    if admin_check:
        return admin_check

    data = request.form

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

        # Camera device (runtime default)
        if 'camera_device' in data:
            try:
                current_app.config['DEFAULT_CAMERA_INDEX'] = int(data.get('camera_device'))
            except Exception:
                pass

        # Session timeout -> PERMANENT_SESSION_LIFETIME (seconds)
        if 'session_timeout' in data:
            try:
                st_min = int(data.get('session_timeout'))
                current_app.config['PERMANENT_SESSION_LIFETIME'] = st_min * 60
            except Exception:
                pass

        # Misc: login_alerts, company_name, company_logo, late_time saved already; optionally mirror to config
        if 'login_alerts' in data:
            current_app.config['LOGIN_ALERT'] = data.get('login_alerts')
        if 'company_name' in data:
            current_app.config['COMPANY_NAME'] = data.get('company_name')
        if 'company_logo' in data:
            current_app.config['COMPANY_LOGO'] = data.get('company_logo')
        if 'late_time' in data:
            current_app.config['LATE_TIME'] = data.get('late_time')
        # Company-wide checkout time (HH:MM) -> CHECKOUT_TIME
        if 'checkout_time' in data:
            current_app.config['CHECKOUT_TIME'] = data.get('checkout_time')
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
    from datetime import datetime
    conn = get_connection()
    cur = conn.cursor()

    # Get company name
    try:
        cur.execute("SELECT setting_value FROM settings WHERE setting_key = 'company_name'")
        company_result = cur.fetchone()
        company_name = company_result[0] if company_result else 'FaceTrack Pro'
    except:
        company_name = 'FaceTrack Pro'

    cur.execute("SELECT * FROM attendance")
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]

    cur.close()
    conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    
    # Add header info
    writer.writerow([company_name])
    writer.writerow([f"Complete Attendance Data Export"])
    writer.writerow([f"Generated on: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"])
    writer.writerow([])  # Blank line
    
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
    from datetime import datetime
    conn = get_connection()
    cur = conn.cursor()

    # Get company name
    try:
        cur.execute("SELECT setting_value FROM settings WHERE setting_key = 'company_name'")
        company_result = cur.fetchone()
        company_name = company_result[0] if company_result else 'FaceTrack Pro'
    except:
        company_name = 'FaceTrack Pro'

    cur.execute("SELECT * FROM employees")
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]

    cur.close()
    conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    
    # Add header info
    writer.writerow([company_name])
    writer.writerow([f"Employee Database Export"])
    writer.writerow([f"Generated on: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"])
    writer.writerow([])  # Blank line
    
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
