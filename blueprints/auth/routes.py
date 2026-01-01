from . import bp
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from utils.extensions import limiter
from .utils import get_user_by_username, verify_password
from db_utils import get_connection
from db_utils import execute, log_audit
from utils.db import get_db
import base64, io, json
from PIL import Image
import numpy as np
from utils.face_encoder import face_encoder


# ============================================================
# LOGIN (Clean – No roles)
# ============================================================
@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    """Username/password authentication - redirects to unified dashboard"""
    if request.method == "POST":
        try:
            username = request.form.get("username")
            password = request.form.get("password")

            if not username or not password:
                flash("Username and password required", "error")
                return redirect(url_for("auth.login"))

            user = get_user_by_username(username)

            if not user or not verify_password(user["password"], password):
                flash("Invalid username or password", "error")
                try:
                    log_audit(user_id=None, action='FAILED_LOGIN', module='auth', details=f'username={username}', ip_address=request.remote_addr)
                except Exception:
                    pass
                return redirect(url_for("auth.login"))

            # Fetch linked employee row (if any)
            db = get_db()
            cur = db.cursor(dictionary=True)
            cur.execute("SELECT * FROM employees WHERE user_id=%s", (user["id"],))
            employee = cur.fetchone()

            # Clear old session and regenerate session ID (prevent session fixation)
            old_session_data = dict(session)  # Preserve any needed data
            session.clear()
            
            # Set new session data
            session["logged_in"] = True
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user.get("role")
            session['employee_id'] = employee['id'] if employee else None
            session['full_name'] = employee['full_name'] if employee and employee.get('full_name') else user.get('username')
            
            # Force session ID regeneration
            session.modified = True

            # Audit successful login
            try:
                log_audit(user_id=user['id'], action='LOGIN', module='auth', details=f'username={username}', ip_address=request.remote_addr)
            except Exception:
                pass

            # Single unified dashboard
            return redirect("/dashboard")

        except Exception as e:
            from utils.logger import logger
            logger.error(f"Login handler error: {e}", exc_info=True)
            flash('Login failed. Please try again.', 'error')
            return redirect(url_for('auth.login'))

    return render_template("login.html")


# During blueprint registration, exempt the specific `login` view from CSRF
# This avoids importing the CSRF instance here and prevents circular imports.
def _exempt_login_record(state):
    try:
        state.app.csrf.exempt(login)
    except Exception:
        # if something is not available, fail silently — blueprint-level
        # exemption may already be applied elsewhere (app.py)
        pass

bp.record(_exempt_login_record)


# ============================================================
# SIGNUP (Clean – No roles)
# ============================================================
@bp.route("/signup", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def signup():
    """User registration - creates account with role-based access"""

    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        username = request.form.get("username")
        phone = request.form.get("phone")
        gender = request.form.get("gender")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        # 1. Password match
        if password != confirm:
            flash("Passwords do not match", "error")
            return redirect(url_for("auth.signup"))
        
        # 2. Password strength validation
        from utils.validators import validate_password, sanitize_email, sanitize_text, sanitize_username
        
        is_strong, msg = validate_password(password)
        if not is_strong:
            flash(msg, "error")
            return redirect(url_for("auth.signup"))
        
        # 3. Sanitize inputs
        clean_email = sanitize_email(email)
        if not clean_email:
            flash("Invalid email format", "error")
            return redirect(url_for("auth.signup"))
        
        clean_username = sanitize_username(username)
        if not clean_username:
            flash("Username must be 3-50 characters (letters, numbers, underscore, hyphen only)", "error")
            return redirect(url_for("auth.signup"))
        
        clean_name = sanitize_text(full_name, max_length=100)
        if not clean_name:
            flash("Full name is required", "error")
            return redirect(url_for("auth.signup"))

        # Default role (no role from UI)
        role = "employee"

        db = get_db()
        cur = db.cursor(dictionary=True)

        # 2. Username exists?
        cur.execute("SELECT * FROM users WHERE username=%s", (clean_username,))
        if cur.fetchone():
            flash("Username already taken", "error")
            return redirect(url_for("auth.signup"))

        # 3. Hash password
        from .utils import hash_password
        hashed = hash_password(password)

        # 4. Insert user
        cur.execute("""
            INSERT INTO users (username, password, role, email)
            VALUES (%s, %s, %s, %s)
        """, (clean_username, hashed, role, clean_email))
        db.commit()

        # 5. Get user ID
        cur.execute("SELECT id FROM users WHERE username=%s", (clean_username,))
        new_user_id = cur.fetchone()["id"]

        # 6. Create employee record (always)
        cur.execute("""
            INSERT INTO employees 
            (user_id, full_name, email, phone, gender, department_id, join_date)
            VALUES (%s, %s, %s, %s, %s, %s, CURDATE())
        """, (new_user_id, clean_name, clean_email, phone, gender, 1))
        db.commit()

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")



# ============================================================
# AUTO ROLE (No longer used, kept for safety)
# ============================================================
@bp.route("/get-role/<username>")
def get_role(username):
    """API endpoint - returns user role for frontend access control"""
    user = get_user_by_username(username)
    return jsonify({"role": user["role"] if user else ""})



# ============================================================
# LOGOUT
# ============================================================
@bp.route("/logout")
def logout():
    """Clear session and redirect to login page"""
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("index"))



# ============================================================
# FACE LOGIN (Clean redirect)
# ============================================================
@bp.route("/face_login", methods=["POST"])
def face_login_api():
    """Face recognition login - matches face embedding to authenticate user"""
    # CSRF protection - validate token from header
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    csrf_token = request.headers.get('X-CSRFToken')
    if not csrf_token:
        return jsonify({"matched": False, "reason": "CSRF token missing"}), 403
    
    try:
        validate_csrf(csrf_token)
    except ValidationError:
        # Audit CSRF failure
        try:
            from db_utils import log_audit
            log_audit(None, 'FACE_LOGIN_CSRF_FAIL', 'auth', 'Invalid CSRF token', request.remote_addr)
        except:
            pass
        return jsonify({"matched": False, "reason": "Invalid CSRF token"}), 403
    
    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"matched": False, "reason": "No image received"})

    try:
        img_str = data["image"].split(",")[1]
        img_bytes = base64.b64decode(img_str)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        frame_rgb = np.array(img)
    except:
        return jsonify({"matched": False, "reason": "Invalid image format"})

    emb = face_encoder.get_embedding(frame_rgb)
    if emb is None:
        # Audit failed attempt - no face
        try:
            from db_utils import log_audit
            log_audit(None, 'FACE_LOGIN_FAILED', 'auth', 'No face detected', request.remote_addr)
        except:
            pass
        return jsonify({"matched": False, "reason": "No face detected"})

    face_encoder.load_all_embeddings()
    result = face_encoder.match(emb)

    if result is None:
        # Audit failed attempt - no match
        try:
            from db_utils import log_audit
            log_audit(None, 'FACE_LOGIN_FAILED', 'auth', 'Face not matched', request.remote_addr)
        except:
            pass
        return jsonify({"matched": False, "reason": "No match"})

    emp_id, distance = result

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT users.id, users.role, employees.full_name
        FROM employees
        JOIN users ON employees.user_id = users.id
        WHERE employees.id = %s
    """, (emp_id,))
    user = cur.fetchone()

    if not user:
        return jsonify({"matched": False, "reason": "Linked user not found"})

    user_id, role, full_name = user

    session.clear()
    session["user_id"] = user_id
    session["emp_id"] = emp_id
    session["full_name"] = full_name
    session["role"] = role
    # Mark the session as authenticated so dashboard checks pass
    session["logged_in"] = True
    
    # Audit successful face login
    try:
        from db_utils import log_audit
        log_audit(user_id, 'FACE_LOGIN_SUCCESS', 'auth', f'emp_id={emp_id} distance={distance:.4f}', request.remote_addr)
    except:
        pass

    # Clean unified redirect
    return jsonify({
        "matched": True,
        "name": full_name,
        "distance": distance,
        "redirect_url": "/dashboard"
    })
