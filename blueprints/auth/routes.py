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


            if employee:
                # STEP 6: Block login if employee is not active
                if employee.get("status") != "active":
                    flash("Your account is inactive. Contact admin.", "danger")
                    return redirect(url_for("auth.logout"))
                session['employee_id'] = employee['id']
                session['full_name'] = employee.get('full_name') or user.get('username')
            else:
                session['employee_id'] = None
                session['full_name'] = user.get('username')
                if user.get('role') == 'employee':
                    flash("Your employee profile is not created yet. Contact admin.", "error")
                    return redirect(url_for('auth.login'))

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

        # PRE-CHECKS: username/email existence (better UX + avoids duplicate inserts)
        cur.execute("SELECT id FROM users WHERE username=%s", (clean_username,))
        if cur.fetchone():
            flash("Username already taken", "error")
            return redirect(url_for("auth.signup"))

        cur.execute("SELECT id FROM users WHERE email=%s", (clean_email,))
        if cur.fetchone():
            flash("Email already registered", "error")
            return redirect(url_for("auth.signup"))

        # 🔴 CHECK: employee must already exist
        cur.execute(
            "SELECT id, user_id FROM employees WHERE email=%s",
            (clean_email,)
        )
        employee = cur.fetchone()
        if not employee:
            flash("Employee record not found. Please contact admin.", "error")
            return redirect(url_for("auth.signup"))
        if employee["user_id"] is not None:
            flash("Account already created for this employee.", "error")
            return redirect(url_for("auth.signup"))

        # 3. Hash password
        from .utils import hash_password
        hashed = hash_password(password)

        try:
            cur.execute("""
                INSERT INTO users (username, password, role, email)
                VALUES (%s, %s, %s, %s)
            """, (clean_username, hashed, role, clean_email))
            user_id = cur.lastrowid
            # 🔗 LINK employee → user
            cur.execute(
                "UPDATE employees SET user_id=%s WHERE id=%s",
                (user_id, employee["id"])
            )
            db.commit()
            flash("Account created! You can now login.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.rollback()
            flash("Signup failed. Please try again.", "error")
            return redirect(url_for("auth.signup"))

    return render_template("signup.html")


# ============================================================
# CURRENT USER API (for employee self-data loading)
# ============================================================
@bp.route("/current-user")
def current_user():
    """API endpoint - returns current logged-in user details"""
    if not session.get("logged_in"):
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    
    return jsonify({
        "status": "ok",
        "user_id": session.get("user_id"),
        "username": session.get("username"),
        "full_name": session.get("full_name"),
        "role": session.get("role"),
        "employee_id": session.get("employee_id")
    })


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
        return jsonify({"matched": False, "reason": "Security validation failed. Please refresh the page."}), 403
    
    try:
        validate_csrf(csrf_token)
    except ValidationError:
        # Audit CSRF failure
        try:
            from db_utils import log_audit
            log_audit(None, 'FACE_LOGIN_CSRF_FAIL', 'auth', 'Invalid CSRF token', request.remote_addr)
        except:
            pass
        return jsonify({"matched": False, "reason": "Security validation failed. Please refresh the page."}), 403
    
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
        return jsonify({"matched": False, "reason": "No face detected in frame"})

    face_encoder.load_all_embeddings()
    result = face_encoder.match(emb)

    if result is None:
        # Audit failed attempt - no match
        try:
            from db_utils import log_audit
            log_audit(None, 'FACE_LOGIN_FAILED', 'auth', 'Face not matched', request.remote_addr)
        except:
            pass
        return jsonify({
            "matched": False, 
            "reason": "Face not enrolled. Please enroll your face first.",
            "not_enrolled": True
        })

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
        return jsonify({"matched": False, "reason": "User account not found. Please contact admin."})

    user_id, role, full_name = user

    session.clear()
    session["user_id"] = user_id
    session["employee_id"] = emp_id
    session["full_name"] = full_name
    session["role"] = role
    session["logged_in"] = True
    session.modified = True
    
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


# ============================================================
# FORGOT PASSWORD - Request Reset Link
# ============================================================
@bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("3 per 15 minutes", methods=["POST"])
def forgot_password():
    """Send password reset email with secure token"""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        
        if not email:
            flash("Please enter your email address", "error")
            return redirect(url_for("auth.forgot_password"))
        
        # Validate email format
        from utils.validators import validate_email
        is_valid, error_msg = validate_email(email)
        if not is_valid:
            flash("Invalid email format", "error")
            return redirect(url_for("auth.forgot_password"))
        
        db = get_db()
        cur = db.cursor(dictionary=True)
        
        # Find user by email
        cur.execute("""
            SELECT u.id, u.username, e.full_name, u.email
            FROM users u
            LEFT JOIN employees e ON e.user_id = u.id
            WHERE u.email = %s
            LIMIT 1
        """, (email,))
        user = cur.fetchone()
        
        # Security: Always show success message (don't reveal if email exists)
        flash("If this email is registered, you will receive a password reset link shortly.", "success")
        
        if not user:
            # Log attempt for security monitoring
            try:
                log_audit(None, 'PASSWORD_RESET_INVALID_EMAIL', 'auth', f'email={email}', request.remote_addr)
            except:
                pass
            return redirect(url_for("auth.login"))
        
        # Generate secure token
        import secrets
        token = secrets.token_urlsafe(32)
        
        # Token expires in 30 minutes
        from datetime import datetime, timedelta
        expires_at = datetime.now() + timedelta(minutes=30)
        
        # Store token in database
        cur.execute("""
            INSERT INTO password_reset_tokens (user_id, token, expires_at, ip_address)
            VALUES (%s, %s, %s, %s)
        """, (user['id'], token, expires_at, request.remote_addr))
        db.commit()
        
        # Send email
        from utils.email_service import email_service
        employee_name = user.get('full_name') or user['username']
        
        try:
            email_service.send_password_reset(email, employee_name, token, expiry_minutes=30)
            log_audit(user['id'], 'PASSWORD_RESET_SENT', 'auth', f'email={email}', request.remote_addr)
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Failed to send password reset email: {e}")
            # Don't reveal error to user for security
        
        return redirect(url_for("auth.login"))
    
    return render_template("forgot_password.html")


# ============================================================
# RESET PASSWORD - Set New Password with Token
# ============================================================
@bp.route("/reset-password", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes", methods=["POST"])
def reset_password():
    """Reset password using token from email"""
    token = request.args.get("token") or request.form.get("token")
    
    if not token:
        flash("Invalid or missing reset token", "error")
        return redirect(url_for("auth.login"))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # Verify token
    from datetime import datetime
    cur.execute("""
        SELECT rt.*, u.username, u.email, e.full_name
        FROM password_reset_tokens rt
        JOIN users u ON rt.user_id = u.id
        LEFT JOIN employees e ON e.user_id = u.id
        WHERE rt.token = %s 
          AND rt.used = 0 
          AND rt.expires_at > %s
        LIMIT 1
    """, (token, datetime.now()))
    
    reset_data = cur.fetchone()
    
    if not reset_data:
        flash("Invalid or expired reset token. Please request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))
    
    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")
        
        if not password or not confirm:
            flash("Both password fields are required", "error")
            return render_template("reset_password.html", token=token)
        
        if password != confirm:
            flash("Passwords do not match", "error")
            return render_template("reset_password.html", token=token)
        
        # Validate password strength
        from utils.validators import validate_password
        is_strong, msg = validate_password(password)
        if not is_strong:
            flash(msg, "error")
            return render_template("reset_password.html", token=token)
        
        # Hash new password
        from .utils import hash_password
        hashed = hash_password(password)
        
        # Update password
        cur.execute("""
            UPDATE users 
            SET password = %s 
            WHERE id = %s
        """, (hashed, reset_data['user_id']))
        
        # Mark token as used
        cur.execute("""
            UPDATE password_reset_tokens 
            SET used = 1 
            WHERE id = %s
        """, (reset_data['id'],))
        
        db.commit()
        
        # Audit log
        try:
            log_audit(reset_data['user_id'], 'PASSWORD_RESET_SUCCESS', 'auth', 
                     f"username={reset_data['username']}", request.remote_addr)
        except:
            pass
        
        flash("Password reset successful! Please login with your new password.", "success")
        return redirect(url_for("auth.login"))
    
    # GET request - show reset form
    return render_template("reset_password.html", token=token, 
                          username=reset_data.get('username'))
