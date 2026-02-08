from flask import Blueprint, session, redirect, url_for, flash, request, jsonify, abort

def check_admin():
    """
    Central admin access check.
    Ensures user is logged in and has 'admin' role.
    Handles both web and API requests.
    """
    # Detect API requests by path
    is_api = '/api/' in request.path or request.is_json or request.accept_mimetypes.best == 'application/json'
    
    if 'user_id' not in session:
        if is_api:
            return jsonify({"error": "Login required"}), 401
        abort(403)  # Show 403 instead of redirecting to login
    if session.get('role') != 'admin':
        if is_api:
            return jsonify({"error": "Admin access required"}), 403
        abort(403)  # Show custom 403 Forbidden page

def check_admin_hr():
    """
    Central admin/hr access check.
    Ensures user is logged in and has 'admin' or 'hr' role.
    Handles both web and API requests.
    """
    # Detect API requests by path
    is_api = request.path.startswith('/admin/reports/api/') or request.is_json or request.accept_mimetypes.best == 'application/json'
    
    if 'user_id' not in session:
        if is_api:
            return jsonify({"error": "Login required"}), 401
        abort(403)  # Show 403 instead of redirecting to login
    if session.get('role') not in ['admin', 'hr']:
        if is_api:
            return jsonify({"error": "Admin/HR access required"}), 403
        abort(403)  # Show custom 403 Forbidden page

def check_employee():
    """
    Central employee access check.
    Ensures user is logged in and has 'employee', 'admin', or 'hr' role.
    Handles both web and API requests.
    """
    # Detect API requests by path
    is_api = '/api/' in request.path or request.is_json or request.accept_mimetypes.best == 'application/json'
    
    if 'user_id' not in session:
        if is_api:
            return jsonify({"error": "Login required"}), 401
        abort(403)  # Show 403 instead of redirecting to login
    if session.get('role') not in ['employee', 'admin', 'hr']:
        if is_api:
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


# ------------------------------------------------------------------
# Development-only helper: set an employee session (admin only)
# Usage: POST /admin/test_set_employee_session { "emp_id": 123 }
# Only enabled when APP_MODE != 'production'. This endpoint is temporary
# and intended for automated integration testing. It requires an admin
# session (blueprint-level `check_admin` already enforces that).
# ------------------------------------------------------------------
from flask import request, session, current_app, jsonify, abort
from utils.db import get_db