from . import bp
from flask import render_template, request, redirect, url_for, session, flash, jsonify
from .utils import get_user_by_username, verify_password
from db_utils import get_connection
from utils.db import get_db
import base64, io, json
from PIL import Image
import numpy as np
from utils.face_encoder import face_encoder


# ============================================================
# LOGIN (Clean – No roles)
# ============================================================
@bp.route("/login", methods=["GET", "POST"])
def login():
    """Username/password authentication - redirects to unified dashboard"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = get_user_by_username(username)

        if not user or not verify_password(user["password"], password):
            flash("Invalid username or password", "error")
            return redirect(url_for("auth.login"))

        # Fetch linked employee row (if any)
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM employees WHERE user_id=%s", (user["id"],))
        employee = cur.fetchone()
        cur.close()
        conn.close()

        # Clear old session
        session.clear()
        session["logged_in"] = True
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user.get("role")
        session['employee_id'] = employee['id'] if employee else None
        session['full_name'] = employee['full_name'] if employee and employee.get('full_name') else user.get('username')

        # Single unified dashboard
        return redirect("/dashboard")

    return render_template("login.html")



# ============================================================
# SIGNUP (Clean – No roles)
# ============================================================
@bp.route("/signup", methods=["GET", "POST"])
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

        # Default role (no role from UI)
        role = "employee"

        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        # 2. Username exists?
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            flash("Username already taken", "error")
            cur.close()
            conn.close()
            return redirect(url_for("auth.signup"))

        # 3. Hash password
        from .utils import hash_password
        hashed = hash_password(password)

        # 4. Insert user
        cur.execute("""
            INSERT INTO users (username, password, role, email)
            VALUES (%s, %s, %s, %s)
        """, (username, hashed, role, email))
        conn.commit()

        # 5. Get user ID
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        new_user_id = cur.fetchone()["id"]

        # 6. Create employee record (always)
        cur.execute("""
            INSERT INTO employees 
            (user_id, full_name, email, phone, gender, department_id, join_date)
            VALUES (%s, %s, %s, %s, %s, %s, CURDATE())
        """, (new_user_id, full_name, email, phone, gender, 1))
        conn.commit()

        cur.close()
        conn.close()

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
    return redirect(url_for("auth.login"))



# ============================================================
# FACE LOGIN (Clean redirect)
# ============================================================
@bp.route("/face_login", methods=["POST"])
def face_login_api():
    """Face recognition login - matches face embedding to authenticate user"""
    """Face recognition login - matches face embedding to authenticate user"""
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
        return jsonify({"matched": False, "reason": "No face detected"})

    face_encoder.load_all_embeddings()
    result = face_encoder.match(emb)

    if result is None:
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

    # Clean unified redirect
    return jsonify({
        "matched": True,
        "name": full_name,
        "distance": distance,
        "redirect_url": "/dashboard"
    })
