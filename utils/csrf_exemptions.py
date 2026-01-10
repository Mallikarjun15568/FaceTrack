# CSRF Exemptions for specific endpoints
# These endpoints are exempted from CSRF protection for functional reasons

def setup_csrf_exemptions(app, csrf):
    """
    Setup selective CSRF exemptions for endpoints that require it.
    Called after all blueprints are registered.
    """

    # Auth: Only exempt face login API (uses token-based auth)
    from blueprints.auth.routes import face_login_api
    csrf.exempt(face_login_api)

    # Kiosk: Exempt recognition endpoints (operates in fullscreen kiosk mode)
    from blueprints.kiosk.routes import (
        kiosk_recognize, liveness_check, verify_pin,
        kiosk_exit, set_kiosk_pin, force_unlock
    )
    csrf.exempt(kiosk_recognize)
    csrf.exempt(liveness_check)
    csrf.exempt(verify_pin)
    csrf.exempt(kiosk_exit)
    csrf.exempt(set_kiosk_pin)
    csrf.exempt(force_unlock)

    # Enroll: Exempt AJAX endpoints for face capture (requires camera access)
    from blueprints.enroll.routes import capture_face, detect_face, update_capture_face
    csrf.exempt(capture_face)
    csrf.exempt(detect_face)
    csrf.exempt(update_capture_face)