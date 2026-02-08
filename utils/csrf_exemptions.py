# CSRF Exemptions for specific endpoints
# These endpoints are exempted from CSRF protection for functional reasons

def setup_csrf_exemptions(app, csrf):
    """
    Setup selective CSRF exemptions for endpoints that require it.
    Called after all blueprints are registered.
    """

    # Kiosk: Exempt all kiosk API endpoints (real-time face recognition and PIN verification)
    from blueprints.kiosk.routes import liveness_check, kiosk_recognize, kiosk_exit, verify_pin, set_kiosk_pin, force_unlock
    csrf.exempt(liveness_check)
    csrf.exempt(kiosk_recognize)
    csrf.exempt(kiosk_exit)
    csrf.exempt(verify_pin)
    csrf.exempt(set_kiosk_pin)
    csrf.exempt(force_unlock)

    # Leave Management: Only exempt adjust_balance (approve/reject now have CSRF protection)
    from blueprints.leave.routes import adjust_balance
    csrf.exempt(adjust_balance)

    # Admin Employee Management: Exempt activate/deactivate endpoints
    from blueprints.admin.employees.routes import activate_employee, deactivate_employee
    csrf.exempt(activate_employee)
    csrf.exempt(deactivate_employee)