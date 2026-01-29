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

    # Settings: Exempt settings API (handles CSRF in form data)
    from blueprints.admin.settings.routes import settings_api
    csrf.exempt(settings_api)

    # Enroll: Exempt face detection (real-time UI feedback, doesn't modify data)
    from blueprints.auth.routes import detect_face
    csrf.exempt(detect_face)