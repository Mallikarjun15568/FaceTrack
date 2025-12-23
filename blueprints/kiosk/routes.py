from flask import render_template, request, jsonify, current_app, session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from . import bp
from .utils import recognize_and_mark
from db_utils import get_setting, set_setting
import time
import random


# ---------------------------------------------------------
# SESSION LOCK: Enforce kiosk-only navigation
# ---------------------------------------------------------
@bp.before_app_request
def enforce_kiosk_lock():
    """If session['in_kiosk'] is True, block navigation to non-kiosk routes."""
    # Skip static files and favicon
    if request.path.startswith('/static/') or request.path == '/favicon.ico':
        return None
    
    if session.get("in_kiosk"):
        # Allow only kiosk routes + exit endpoint + admin routes
        allowed = ["/kiosk/", "/kiosk/recognize", "/kiosk/exit", "/kiosk/api/status", "/kiosk/admin/"]
        if not any(request.path.startswith(route) for route in allowed):
            return redirect(url_for("kiosk.kiosk_page"))


# ---------------------------------------------------------
# UI PAGE
# ---------------------------------------------------------
@bp.route("/")
def kiosk_page():
    """Kiosk mode UI - full-screen attendance capture"""
    # Set kiosk lock when entering kiosk mode
    session["in_kiosk"] = True
    
    # Skip liveness - direct recognition mode
    session["lv_pass"] = True
    
    return render_template("kiosk.html")


# ---------------------------------------------------------
# LIVENESS CHECK API
# ---------------------------------------------------------
@bp.route("/liveness_check", methods=["POST"])
def liveness_check():
    """Simple face detection check - no liveness required"""
    try:
        from utils.face_encoder import face_encoder
        import base64
        import numpy as np
        import cv2
        
        data = request.get_json()
        frame_b64 = data.get("frame")
        
        # Decode frame
        img_bytes = base64.b64decode(frame_b64.split(",")[1] if "," in frame_b64 else frame_b64)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({"success": False, "message": "Invalid frame"}), 400
        
        # Get face analysis from InsightFace
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_encoder.app.get(rgb)
        
        # Simple face detection - if face found, pass immediately
        if faces is None or len(faces) == 0:
            return jsonify({
                "success": False,
                "lv_pass": False,
                "message": "Position your face in the frame",
                "progress": 0
            })
        
        # Face detected - auto-pass liveness
        session["lv_pass"] = True
        
        return jsonify({
            "success": True,
            "lv_pass": True,
            "message": "Face detected ✓",
            "progress": 100
        })
    
    except Exception:
        return jsonify({"success": False, "message": "Server error"}), 500


# ---------------------------------------------------------
# BACKEND RECOGNITION API
# ---------------------------------------------------------
@bp.route("/recognize", methods=["POST"])
def kiosk_recognize():
    """Face recognition + attendance marking (requires liveness pass)"""
    try:
        # Check if liveness was passed
        if not session.get("lv_pass", False):
            return jsonify({
                "status": "error",
                "message": "Liveness check required"
            }), 403
        
        data = request.get_json()
        frame_b64 = data.get("frame")

        result = recognize_and_mark(frame_b64, current_app)
        
        # Reset liveness after successful recognition
        if result.get("status") == "matched":
            session["lv_pass"] = False
            session["liveness_attempts"] = 0
            session["liveness_challenge"] = random.choice(["blink", "head_left", "head_right"])
        
        return jsonify(result)

    except Exception:
        return jsonify({"status": "error", "message": "Recognition failed"}), 500


# ---------------------------------------------------------
# EXIT KIOSK (PIN Protected)
# ---------------------------------------------------------
@bp.route("/exit", methods=["GET", "POST"])
def kiosk_exit():
    """Exit kiosk mode - requires PIN authentication to prevent unauthorized exit"""
    if request.method == "GET":
        # Redirect GET requests to the kiosk UI — we use the PIN modal there.
        return redirect(url_for("kiosk.kiosk_page"))

    # POST: Verify PIN
    data = request.get_json()
    pin = data.get("pin", "")

    # Brute-force protection
    lockout_until = session.get("pin_lockout_until", 0)
    if time.time() < lockout_until:
        remaining = int(lockout_until - time.time())
        return jsonify({"success": False, "message": f"Locked out. Try again in {remaining}s"}), 403

    # Get stored PIN hash
    pin_hash = get_setting("kiosk_pin_hash")
    if not pin_hash or pin_hash == "NULL":
        return jsonify({"success": False, "message": "No PIN set. Contact admin."}), 403

    # Verify PIN
    try:
        pin_valid = check_password_hash(pin_hash, pin)
    except Exception as e:
        return jsonify({"success": False, "message": "PIN verification error."}), 500
    
    if pin_valid:
        session.pop("in_kiosk", None)
        session["pin_attempts"] = 0
        return jsonify({"success": True, "redirect": "/dashboard"})
    else:
        attempts = session.get("pin_attempts", 0) + 1
        session["pin_attempts"] = attempts

        if attempts >= 5:
            session["pin_lockout_until"] = time.time() + 300  # 5 min lockout
            session["pin_attempts"] = 0
            return jsonify({"success": False, "message": "Too many attempts. Locked for 5 minutes."}), 403

        return jsonify({"success": False, "message": f"Incorrect PIN. {5 - attempts} attempts left."}), 401


# ---------------------------------------------------------
# VERIFY PIN (for UI-only checks, does NOT exit kiosk)
# ---------------------------------------------------------
@bp.route("/verify_pin", methods=["POST"])
def verify_pin():
    """Verify PIN without exiting kiosk mode (used by kiosk UI to unlock settings)."""
    data = request.get_json()
    pin = data.get("pin", "")

    # Brute-force protection (reuse same session keys)
    lockout_until = session.get("pin_lockout_until", 0)
    if time.time() < lockout_until:
        remaining = int(lockout_until - time.time())
        return jsonify({"success": False, "message": f"Locked out. Try again in {remaining}s"}), 403

    # Get stored PIN hash
    pin_hash = get_setting("kiosk_pin_hash")
    if not pin_hash or pin_hash == "NULL":
        return jsonify({"success": False, "message": "No PIN set. Contact admin."}), 403

    # Verify PIN
    try:
        pin_valid = check_password_hash(pin_hash, pin)
    except Exception:
        return jsonify({"success": False, "message": "PIN verification error."}), 500

    if pin_valid:
        session["pin_attempts"] = 0
        return jsonify({"success": True, "message": "PIN verified."})
    else:
        attempts = session.get("pin_attempts", 0) + 1
        session["pin_attempts"] = attempts

        if attempts >= 5:
            session["pin_lockout_until"] = time.time() + 300  # 5 min lockout
            session["pin_attempts"] = 0
            return jsonify({"success": False, "message": "Too many attempts. Locked for 5 minutes."}), 403

        return jsonify({"success": False, "message": f"Incorrect PIN. {5 - attempts} attempts left."}), 401


# ---------------------------------------------------------
# ADMIN: Set Kiosk PIN
# ---------------------------------------------------------
@bp.route("/admin/set_pin", methods=["POST"])
def set_kiosk_pin():
    """Admin endpoint - set/update kiosk exit PIN"""
    # Admin-only check
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Admin access required."}), 403

    data = request.get_json()
    new_pin = data.get("pin", "")

    # Validation
    if not new_pin.isdigit() or len(new_pin) < 4:
        return jsonify({"success": False, "message": "PIN must be at least 4 digits."}), 400

    # Hash and store
    pin_hash = generate_password_hash(new_pin)
    if set_setting("kiosk_pin_hash", pin_hash):
        return jsonify({"success": True, "message": "Kiosk PIN updated successfully."})
    else:
        return jsonify({"success": False, "message": "Database error."}), 500


# ---------------------------------------------------------
# API: Check Kiosk Status
# ---------------------------------------------------------
@bp.route("/api/status", methods=["GET"])
def kiosk_status():
    """Check if kiosk mode is active and PIN is configured"""
    return jsonify({
        "locked": session.get("in_kiosk", False),
        "pin_set": bool(get_setting("kiosk_pin_hash"))
    })


# ---------------------------------------------------------
# ADMIN: Force Unlock Kiosk
# ---------------------------------------------------------
@bp.route("/admin/force_unlock", methods=["POST"])
def force_unlock():
    """Admin emergency unlock - bypass PIN requirement to exit kiosk mode"""
    # Admin-only check
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Admin access required."}), 403
    
    # Clear kiosk lock
    session.pop("in_kiosk", None)
    session.pop("pin_attempts", None)
    session.pop("pin_lockout_until", None)
    
    return jsonify({"success": True, "message": "Kiosk unlocked remotely."})
