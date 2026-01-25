from flask import Blueprint, session, redirect, url_for, flash, request, jsonify, abort

def check_admin():
    """
    Central admin access check.
    Ensures user is logged in and has 'admin' role.
    Handles both web and API requests.
    """
    if 'user_id' not in session:
        if request.is_json:
            return jsonify({"error": "Login required"}), 401
        abort(403)  # Show 403 instead of redirecting to login
    if session.get('role') != 'admin':
        if request.is_json:
            return jsonify({"error": "Admin access required"}), 403
        abort(403)  # Show custom 403 Forbidden page

def check_admin_hr():
    """
    Central admin/hr access check.
    Ensures user is logged in and has 'admin' or 'hr' role.
    Handles both web and API requests.
    """
    if 'user_id' not in session:
        if request.is_json:
            return jsonify({"error": "Login required"}), 401
        abort(403)  # Show 403 instead of redirecting to login
    if session.get('role') not in ['admin', 'hr']:
        if request.is_json:
            return jsonify({"error": "Admin/HR access required"}), 403
        abort(403)  # Show custom 403 Forbidden page

def check_employee():
    """
    Central employee access check.
    Ensures user is logged in and has 'employee', 'admin', or 'hr' role.
    Handles both web and API requests.
    """
    if 'user_id' not in session:
        if request.is_json:
            return jsonify({"error": "Login required"}), 401
        abort(403)  # Show 403 instead of redirecting to login
    if session.get('role') not in ['employee', 'admin', 'hr']:
        if request.is_json:
            return jsonify({"error": "Employee/Admin/HR access required"}), 403
        abort(403)  # Show custom 403 Forbidden page

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

admin_bp.before_request(check_admin)
from .employees import bp as employees_bp
admin_bp.register_blueprint(employees_bp, url_prefix="/employees")

from .reports import bp as reports_bp
admin_bp.register_blueprint(reports_bp, url_prefix="/reports")

from .dashboard import bp as dashboard_bp
admin_bp.register_blueprint(dashboard_bp, url_prefix="/dashboard")

from .settings import bp as settings_bp
admin_bp.register_blueprint(settings_bp, url_prefix="/settings")