# auth/utils.py
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, redirect, flash, url_for
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
            flash("Please login first", "error")
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
            user_role = session.get("role")

            if user_role not in roles:
                flash("Access denied", "error")
                return redirect(url_for("auth.login"))

            return f(*args, **kwargs)
        return wrapper
    return decorator
