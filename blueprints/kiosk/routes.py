from flask import render_template, request, jsonify, current_app, session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from markupsafe import escape
from blueprints.auth.utils import login_required, role_required
from . import bp
from .utils import recognize_and_mark, decode_frame
from utils.liveness_detector import LivenessDetector
from db_utils import get_setting, set_setting
from utils.logger import logger
import time
import random
import re

# Input sanitization helper
def sanitize_pin(pin):
    """Validate and sanitize PIN input - digits only"""
    if not pin or not isinstance(pin, str):
        return None
    # Remove non-digits
    clean = re.sub(r'[^0-9]', '', pin)
    if len(clean) < 4 or len(clean) > 8:
        return None
    return clean


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
        # Strict whitelist - only essential kiosk routes
        allowed_exact = ["/kiosk/", "/kiosk/exit"]
        allowed_prefixes = ["/kiosk/recognize", "/kiosk/api/", "/kiosk/liveness_check", "/kiosk/verify_pin"]
        
        # Check exact matches first
        if request.path in allowed_exact:
            return None
        
        # Check prefix matches
        if any(request.path.startswith(prefix) for prefix in allowed_prefixes):
            return None
        
        # Block everything else (including /kiosk/admin/* during lock)
        logger.warning(f"Blocked kiosk navigation attempt to: {request.path}")
        return redirect(url_for("kiosk.kiosk_page"))


# --- Global liveness detector (single instance for the blueprint) ---
liveness = LivenessDetector()


# ---------------------------------------------------------
# UI PAGE
# ---------------------------------------------------------
@bp.route("/")
def kiosk_page():
    """Kiosk mode UI - full-screen attendance capture"""
    # Set kiosk lock when entering kiosk mode
    session["in_kiosk"] = True
    
    # Reset liveness on page load - require fresh liveness check
    session.pop("lv_pass", None)
    liveness.reset()  # Clear liveness detector state
    
    return render_template("kiosk.html")


# ---------------------------------------------------------
# LIVENESS CHECK API
# ---------------------------------------------------------
@bp.route("/liveness_check", methods=["POST"])
def liveness_check():
    """Real liveness detection - prevents photo/video spoofing"""
    try:
        data = request.get_json()
        frame_b64 = data.get("frame")

        # Use centralized decoder
        try:
            pil_img, frame = decode_frame(frame_b64)
        except Exception:
            frame = None

        if frame is None:
            return jsonify({"success": False, "message": "Invalid frame"}), 400
        
        # ACTUAL LIVENESS DETECTION using LivenessDetector
        is_live, confidence, message = liveness.check_liveness(frame)
        
        if not is_live:
            return jsonify({
                "success": False,
                "lv_pass": False,
                "message": message,
                "confidence": float(confidence),
                "progress": int(confidence * 100)
            })
        
        # Liveness passed - set session flag
        session["lv_pass"] = True
        
        return jsonify({
            "success": True,
            "lv_pass": True,
            "message": "Liveness verified ✓",
            "confidence": float(confidence),
            "progress": 100
        })
    
    except Exception as e:
        logger.error(f"Liveness check error: {e}", exc_info=True)
        return jsonify({"success": False, "message": "Server error"}), 500


# ---------------------------------------------------------
# BACKEND RECOGNITION API
# ---------------------------------------------------------
@bp.route("/recognize", methods=["POST"])
def kiosk_recognize():
    """Face recognition + attendance marking (requires liveness pass)"""
    try:
        import base64
        import numpy as np
        import cv2
        import traceback

        data = request.get_json()
        frame_b64 = data.get("frame")

        # --- SAFE FRAME DECODE (central helper) ---
        try:
            pil_img, frame = decode_frame(frame_b64)
        except Exception:
            frame = None

        # If camera/frame not yet ready, return WAIT (do not proceed)
        if frame is None:
            return jsonify({
                "status": "WAIT",
                "message": "Camera frame not ready"
            }), 200

        # --- LIVENESS CHECK ---
        is_live, confidence, message = liveness.check_liveness(frame)

        if not is_live:
            return jsonify({
                "status": "WAIT",
                "message": message
            }), 200

        # --- RECOGNITION (only when liveness passed) ---
        result = recognize_and_mark(frame_b64, current_app)

        # Log the result for debugging
        logger.info(f"Kiosk recognition result: {result}")

        # If no structured result returned, ask client to keep scanning
        if not result or not isinstance(result, dict):
            return jsonify({
                "status": "WAIT",
                "message": "Face not matched yet"
            }), 200

        # Reset liveness detector after successful attendance marking
        if result.get("status") in ("check-in", "check-out"):
            liveness.reset()

        # Attach liveness details so frontend can show confidence/meta
        try:
            if isinstance(result, dict):
                result.setdefault('liveness_confidence', float(confidence))
                result.setdefault('liveness_message', str(message))
        except Exception:
            pass

        return jsonify(result), 200

    except Exception as e:
        # Defensive: log error but never return 500 to kiosk frontend
        logger.error(f"Kiosk recognition error: {e}", exc_info=True)
        return jsonify({
            "status": "ERROR",
            "message": "Internal processing error"
        }), 200


# ---------------------------------------------------------
# EXIT KIOSK (PIN Protected)
# ---------------------------------------------------------
@bp.route("/exit", methods=["GET", "POST"])
def kiosk_exit():
    """Exit kiosk mode - requires PIN authentication to prevent unauthorized exit"""
    logger.info(f"[DEBUG] Kiosk exit request - Method: {request.method}, Session in_kiosk: {session.get('in_kiosk')}")
    
    if request.method == "GET":
        # Redirect GET requests to the kiosk UI — we use the PIN modal there.
        return redirect(url_for("kiosk.kiosk_page"))

    # POST: Verify PIN
    data = request.get_json()
    pin_raw = data.get("pin", "")
    
    logger.info(f"[DEBUG] Exit PIN attempt - PIN length: {len(pin_raw) if pin_raw else 0}")
    
    # Sanitize PIN input (digits only)
    pin = sanitize_pin(pin_raw)
    if pin is None:
        logger.warning("Invalid PIN format")
        return jsonify({"success": False, "message": "Invalid PIN format"}), 400

    # Stricter brute-force protection
    MAX_PIN_ATTEMPTS = 3
    LOCKOUT_DURATION = 900  # 15 minutes
    
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
        logger.info(f"[DEBUG] PIN validation result: {pin_valid}")
    except Exception as e:
        logger.error(f"PIN verification error: {e}", exc_info=True)
        return jsonify({"success": False, "message": "PIN verification error."}), 500
    
    if pin_valid:
        logger.info("[SUCCESS] PIN valid - Exiting kiosk mode")
        session.pop("in_kiosk", None)
        session["pin_attempts"] = 0
        session.pop("pin_lockout_until", None)
        
        # For security: Force re-login after kiosk exit to prevent PIN abuse
        from blueprints.auth.routes import logout
        logout()
        
        return jsonify({"success": True, "redirect": "/"})
    else:
        attempts = session.get("pin_attempts", 0) + 1
        session["pin_attempts"] = attempts
        
        # Audit failed PIN attempt
        try:
            from db_utils import log_audit
            attempts_left = MAX_PIN_ATTEMPTS - attempts
            log_audit(None, 'KIOSK_PIN_FAILED', 'kiosk', f'attempts_left={attempts_left} ip={request.remote_addr}', request.remote_addr)
        except:
            pass

        if attempts >= MAX_PIN_ATTEMPTS:
            session["pin_lockout_until"] = time.time() + LOCKOUT_DURATION
            session["pin_attempts"] = 0
            
            # Audit lockout event
            try:
                from db_utils import log_audit
                log_audit(None, 'KIOSK_PIN_LOCKOUT', 'kiosk', f'duration={LOCKOUT_DURATION}s ip={request.remote_addr}', request.remote_addr)
            except:
                pass
            
            logger.warning(f"Kiosk PIN lockout triggered from IP: {request.remote_addr}")
            return jsonify({"success": False, "message": f"Too many attempts. Locked for {LOCKOUT_DURATION//60} minutes."}), 403

        return jsonify({"success": False, "message": f"Incorrect PIN. {MAX_PIN_ATTEMPTS - attempts} attempts left."}), 401


# ---------------------------------------------------------
# VERIFY PIN (for UI-only checks, does NOT exit kiosk)
# ---------------------------------------------------------
@bp.route("/verify_pin", methods=["POST"])
def verify_pin():
    """Verify PIN without exiting kiosk mode (used by kiosk UI to unlock settings)."""
    data = request.get_json()
    pin_raw = data.get("pin", "")
    
    # Sanitize PIN input
    pin = sanitize_pin(pin_raw)
    if pin is None:
        return jsonify({"success": False, "message": "Invalid PIN format"}), 400

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
@role_required("admin")
def set_kiosk_pin():
    """Admin endpoint - set/update kiosk exit PIN"""
    
    data = request.get_json()
    new_pin_raw = data.get("pin", "")
    
    # Sanitize and validate PIN
    new_pin = sanitize_pin(new_pin_raw)
    if new_pin is None or len(new_pin) < 4:
        return jsonify({"success": False, "message": "PIN must be 4-8 digits only."}), 400

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
@role_required("admin")
def force_unlock():
    """Admin emergency unlock - bypass PIN requirement to exit kiosk mode"""
    
    # Audit force unlock action
    try:
        from db_utils import log_audit
        admin_id = session.get("user_id")
        log_audit(admin_id, 'KIOSK_FORCE_UNLOCK', 'kiosk', f'admin_id={admin_id} ip={request.remote_addr}', request.remote_addr)
    except:
        pass
    
    # Clear kiosk lock
    session.pop("in_kiosk", None)
    session.pop("pin_attempts", None)
    session.pop("pin_lockout_until", None)
    
    return jsonify({"success": True, "message": "Kiosk unlocked remotely."})
