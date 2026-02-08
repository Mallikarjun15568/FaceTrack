# auth/utils.py
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, redirect, flash, url_for, jsonify, request
from db_utils import get_connection


# -----------------------------------------------------------
# 🔐 PASSWORD HASHING + VERIFY (secure)
# -----------------------------------------------------------

def hash_password(password: str) -> str:
    """Generate a hashed password (secure)."""
    return generate_password_hash(password)


def verify_password(stored_hash: str, password: str) -> bool:
    """Verify plain password with stored hash."""
    return check_password_hash(stored_hash, password)


# -----------------------------------------------------------
# 📌 GET USER FROM DB
# -----------------------------------------------------------

def get_user_by_username(username: str):
    """Fetch a single user row by username."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    return user


# -----------------------------------------------------------
# 🛡 LOGIN REQUIRED DECORATOR
# -----------------------------------------------------------

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            # Check if this is an API request (expects JSON response)
            if request.path.startswith('/admin/reports/api/') or request.path.startswith('/api/'):
                return jsonify({"success": False, "error": "Authentication required", "status": "unauthorized"}), 401
            
            flash("Please login first", "error")
            # Check if this is an employee route, redirect accordingly
            if request.endpoint and request.endpoint.startswith("employee."):
                return redirect(url_for("auth.user_login"))
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


# -----------------------------------------------------------
# 🛡 ROLE REQUIRED DECORATOR
# -----------------------------------------------------------

def role_required(*roles):
    """
    Usage:
    @role_required('admin')
    @role_required('admin', 'hr')
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Check if this is an API request
            is_api_request = request.path.startswith('/admin/reports/api/') or request.path.startswith('/api/')
            
            # First check if user is logged in
            if not session.get("logged_in"):
                if is_api_request:
                    return jsonify({"success": False, "error": "Authentication required", "status": "unauthorized"}), 401
                
                flash("Please login first", "error")
                # Check if this is an employee route, redirect accordingly
                if request.endpoint and request.endpoint.startswith("employee."):
                    return redirect(url_for("auth.user_login"))
                return redirect(url_for("auth.login"))
            
            user_role = session.get("role")

            if user_role not in roles:
                if is_api_request:
                    return jsonify({"success": False, "error": "Access denied", "status": "forbidden"}), 403
                
                flash("⛔ Access Denied: You don't have permission to access this page", "error")
                # Redirect based on role
                if user_role == "employee":
                    return redirect(url_for("employee.dashboard"))
                return redirect(url_for("auth.login"))

            return f(*args, **kwargs)
        return wrapper
    return decorator
