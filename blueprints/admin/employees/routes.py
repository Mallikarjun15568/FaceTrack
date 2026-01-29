"""
# ============================================================
# IMPORTS (MUST BE FIRST)
# ============================================================
"""
from . import bp
from flask import (
    render_template, request, redirect,
    url_for, flash, session, jsonify, current_app
)
import os
import cv2
import numpy as np
import shutil
import math
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.db import get_db
from utils.face_encoder import face_encoder, invalidate_embeddings_cache
from utils.logger import logger
from db_utils import log_audit
from blueprints.auth.utils import login_required, role_required
from utils.email_service import EmailService
from utils.helpers import ensure_folder

# ============================================================
# DEACTIVATE EMPLOYEE (SOFT DELETE)
# ============================================================
@bp.route("/deactivate/<int:emp_id>", methods=["POST"])
@login_required
@role_required("admin", "hr")
def deactivate_employee(emp_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE employees
        SET status = 'inactive'
        WHERE id = %s
    """, (emp_id,))
    db.commit()

    log_audit(
        user_id=session.get("user_id"),
        action="EMPLOYEE_DEACTIVATED",
        module="employees",
        details=f"Employee ID {emp_id} deactivated",
        ip_address=request.remote_addr
    )

    return jsonify({"success": True})

# ============================================================
# ACTIVATE EMPLOYEE
# ============================================================
@bp.route("/activate/<int:emp_id>", methods=["POST"])
@login_required
@role_required("admin", "hr")
def activate_employee(emp_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        UPDATE employees
        SET status = 'active'
        WHERE id = %s
    """, (emp_id,))
    db.commit()

    log_audit(
        user_id=session.get("user_id"),
        action="EMPLOYEE_ACTIVATED",
        module="employees",
        details=f"Employee ID {emp_id} activated",
        ip_address=request.remote_addr
    )

    return jsonify({"success": True})



# ============================================================
# EMPLOYEE LIST PAGE
# ============================================================
@bp.route("/", methods=["GET"])
@login_required
@role_required("admin", "hr")
def list_employees():
    db = get_db()
    cursor = db.cursor(dictionary=True)


    department_id = request.args.get("department_id")
    enrolled = request.args.get("enrolled")
    sort = request.args.get("sort", "newest")
    search = request.args.get("search", "").strip()

    # STEP 3: Status filter (default active)
    status_filter = request.args.get("status", "all")

    page = int(request.args.get("page", 1))
    per_page = 10
    offset = (page - 1) * per_page

    where_clauses = []
    params = []

    # Search filter
    if search:
        where_clauses.append("(e.full_name LIKE %s OR e.email LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])

    # 🔧 FIX 1: Department filter
    if department_id:
        where_clauses.append("e.department_id = %s")
        params.append(department_id)

    if enrolled == "enrolled":
        where_clauses.append("fd.embedding IS NOT NULL")
    elif enrolled == "not_enrolled":
        where_clauses.append("fd.embedding IS NULL")

    # STEP 3: Status filter logic
    if status_filter != "all":
        where_clauses.append("e.status = %s")
        params.append(status_filter)

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Update total count query to include face_data join
    count_query = "SELECT COUNT(*) AS total FROM employees e LEFT JOIN face_data fd ON fd.emp_id = e.id " + where_sql
    cursor.execute(count_query, tuple(params))
    total = cursor.fetchone()["total"]

    # Calculate total pages
    total_pages = math.ceil(total / per_page) if total > 0 else 1

    order_by = "e.id DESC"
    if sort == "oldest":
        order_by = "e.id ASC"
    elif sort == "name_asc":
        order_by = "e.full_name ASC"
    elif sort == "name_desc":
        order_by = "e.full_name DESC"

    query = (
        """
        SELECT 
            e.id, 
            e.full_name, 
            e.email, 
            e.phone,
            e.gender,
            e.job_title,
            e.join_date, 
            e.status,
            d.name AS department,
            CASE 
                WHEN fd.embedding IS NOT NULL THEN 1
                ELSE 0
            END AS enrolled
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        LEFT JOIN face_data fd ON fd.emp_id = e.id
        """
        + where_sql
        + "\n        ORDER BY "
        + order_by
        + "\n        LIMIT %s OFFSET %s"
    )

    cursor.execute(query, tuple(params) + (per_page, offset))
    employees = cursor.fetchall()

    cursor.execute("SELECT id, name FROM departments")
    departments = cursor.fetchall()

    qs = request.query_string.decode("utf-8")

    return render_template(
        "employees.html",
        employees=employees,
        departments=departments,
        total=total,
        total_pages=total_pages,
        page=page,
        per_page=per_page,
        start=offset,
        end=offset + len(employees),
        querystring=qs,
        sort=sort,
        search=search,
        current_role=session.get("role")
    )


# ============================================================
# ADD EMPLOYEE
# ============================================================
@bp.route("/add", methods=["GET", "POST"])
@login_required
@role_required("admin", "hr")
def add_employee():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "GET":
        cursor.execute("SELECT * FROM departments")
        departments = cursor.fetchall()
        return render_template("add_employee.html", departments=departments)

    # ✅ START TRANSACTION
    try:
        db.start_transaction()
    except AttributeError:
        # Fallback for older MySQL connector versions
        pass

    try:
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone", "")
        gender = request.form.get("gender")
        department_id = request.form.get("department_id")
        job_title = request.form.get("job_title")
        join_date = request.form.get("join_date")
        status = "active"

        # Validate email format
        from utils.validators import validate_email
        is_valid_email, email_error = validate_email(email)
        if not is_valid_email:
            db.rollback()
            flash(f"Invalid email: {email_error}", "danger")
            return redirect(url_for("employees.add_employee"))

        photo_file = request.files.get("photo")

        if not photo_file:
            db.rollback()
            flash("Please upload a photo!", "danger")
            return redirect(url_for("employees.add_employee"))
        
        # Validate file upload
        from utils.validators import validate_image_upload
        is_valid, error_msg = validate_image_upload(photo_file)
        if not is_valid:
            db.rollback()
            flash(f"Photo upload failed: {error_msg}", "danger")
            return redirect(url_for("employees.add_employee"))

        # PRE-CHECK: avoid duplicate employee by email
        cursor.execute("SELECT id FROM employees WHERE email=%s", (email,))
        if cursor.fetchone():
            db.rollback()
            flash("Employee with this email already exists", "danger")
            return redirect(url_for("employees.add_employee"))

        # ❌ NO COMMIT HERE - Insert employee without committing
        from mysql.connector import IntegrityError
        cursor.execute("""
            INSERT INTO employees (full_name, email, phone, gender, job_title, department_id, join_date, status, photo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, '')
        """, (full_name, email, phone, gender, job_title, department_id, join_date, status))
        # ❌ NO db.commit() HERE

        employee_id = cursor.lastrowid

        # Save photo to disk
        folder_path = f"static/uploads/employees/{employee_id}/"
        os.makedirs(folder_path, exist_ok=True)

        filename = secure_filename(photo_file.filename)
        image_path = os.path.join(folder_path, filename)
        photo_file.save(image_path)

        # Process face embedding
        img = cv2.imread(image_path)
        if img is None:
            db.rollback()
            # 🔧 FIX 3: Filesystem cleanup on rollback
            if os.path.exists(image_path):
                os.remove(image_path)
            flash("Failed to read uploaded photo!", "danger")
            return redirect(url_for("employees.add_employee"))

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        embedding = face_encoder.get_embedding(rgb)

        if embedding is None:
            db.rollback()
            # 🔧 FIX 3: Filesystem cleanup on rollback
            if os.path.exists(image_path):
                os.remove(image_path)
            flash("No face detected in the photo!", "danger")
            logger.warning(f"No face detected in uploaded photo for employee: {full_name}")
            return redirect(url_for("employees.add_employee"))

        # Store embedding in face_data table (512-dim float32)
        embedding_bytes = embedding.astype(np.float32).tobytes()
        
        # Update employee photo path
        cursor.execute("""
            UPDATE employees
            SET photo=%s
            WHERE id=%s
        """, (image_path, employee_id))
        
        # Insert into face_data table
        cursor.execute("""
            INSERT INTO face_data (emp_id, embedding, image_path, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (employee_id, embedding_bytes, image_path))
        
        # Create leave_balance row for new employee (MANDATORY for admin credit to work)
        cursor.execute("""
            INSERT INTO leave_balance (employee_id, casual_leave, sick_leave, vacation_leave, emergency_leave)
            VALUES (%s, 0, 0, 0, 0)
        """, (employee_id,))
        
        # ✅ SINGLE COMMIT - Only at the end after all operations
        db.commit()

        # Invalidate cache so new embedding is loaded
        invalidate_embeddings_cache()

        # Audit log
        log_audit(
            user_id=session.get('user_id'),
            action='EMPLOYEE_ADDED',
            module='employees',
            details=f'Added employee: {full_name} (ID: {employee_id})',
            ip_address=request.remote_addr
        )

        flash("Employee added successfully!", "success")
        logger.info(f"Employee added: {full_name} (ID: {employee_id})")
        return redirect(url_for("employees.list_employees"))
        
    except IntegrityError as e:
        # ✅ ROLLBACK on database constraint error
        db.rollback()
        # 🔧 FIX 3: Filesystem cleanup on rollback
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)
        logger.error(f"Database integrity error adding employee: {e}", exc_info=True)
        flash("Failed to add employee due to database constraint.", "danger")
        return redirect(url_for("employees.add_employee"))
    except Exception as e:
        # ✅ ROLLBACK on any other error
        db.rollback()
        # 🔧 FIX 3: Filesystem cleanup on rollback
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)
        logger.error(f"Error adding employee: {e}", exc_info=True)
        flash(f"Error adding employee: {str(e)}", "danger")
        return redirect(url_for("employees.add_employee"))


# ============================================================
# DELETE EMPLOYEE
# ============================================================




# ============================================================
# VIEW EMPLOYEE
# ============================================================
@bp.route("/view/<int:emp_id>")
@login_required
@role_required("admin", "hr")
def view_employee(emp_id):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT e.*, d.name AS department
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        WHERE e.id = %s
    """, (emp_id,))
    emp = cursor.fetchone()

    if not emp:
        return "Employee not found"

    return render_template("employee_view.html", emp=emp)


# ============================================================
# USER MANAGEMENT (Admin Role Assignment)
# ============================================================
@bp.route("/users", methods=["GET"])
@login_required
@role_required("admin", "hr")
def user_management():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get search and filter params
    search = request.args.get("search", "").strip()
    role_filter = request.args.get("role", "all")
    page = int(request.args.get("page", 1))
    per_page = 10
    offset = (page - 1) * per_page

    # Build query
    where_clauses = []
    params = []

    if search:
        where_clauses.append("(u.username LIKE %s OR u.email LIKE %s)")
        params.extend([f"%{search}%", f"%{search}%"])

    if role_filter != "all":
        where_clauses.append("u.role = %s")
        params.append(role_filter)

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Count total
    count_query = f"SELECT COUNT(*) as total FROM users u {where_sql}"
    cursor.execute(count_query, tuple(params))
    total = cursor.fetchone()["total"]

    # Get users
    query = f"""
        SELECT u.id, u.username, u.email, u.role,
               e.full_name, e.id as employee_id
        FROM users u
        LEFT JOIN employees e ON u.id = e.user_id
        {where_sql}
        ORDER BY u.id DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, tuple(params) + (per_page, offset))
    users = cursor.fetchall()

    # Get role options
    cursor.execute("SELECT DISTINCT role FROM users ORDER BY role")
    roles = [row["role"] for row in cursor.fetchall()]

    return render_template("user_management.html",
                         users=users,
                         roles=roles,
                         search=search,
                         role_filter=role_filter,
                         page=page,
                         per_page=per_page,
                         total=total,
                         total_pages=(total + per_page - 1) // per_page,  # Calculate total pages
                         min=min,
                         max=max,
                         range=range)


@bp.route("/users/change-role/<int:user_id>", methods=["POST"])
@login_required
@role_required("admin", "hr")
def change_user_role(user_id):
    new_role = request.form.get("role")
    valid_roles = ["admin", "hr", "employee"]
    current_user_id = session.get("user_id")
    current_user_role = session.get("role")

    if new_role not in valid_roles:
        flash("Invalid role", "error")
        return redirect(url_for("employees.user_management"))

    # Security checks
    if user_id == current_user_id:
        flash("You cannot change your own role", "error")
        return redirect(url_for("employees.user_management"))

    # Only admins can assign admin role
    if new_role == "admin" and current_user_role != "admin":
        flash("Only administrators can assign admin role", "error")
        return redirect(url_for("employees.user_management"))

    db = get_db()
    cursor = db.cursor()

    # Prevent demoting the last admin
    if new_role != "admin":
        cursor.execute("SELECT COUNT(*) as admin_count FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        current_role = cursor.fetchone()[0]
        
        if current_role == "admin" and admin_count <= 1:
            flash("Cannot demote the last administrator", "error")
            return redirect(url_for("employees.user_management"))

    # Update role
    cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
    db.commit()

    # Audit log
    log_audit(
        user_id=current_user_id,
        action="USER_ROLE_CHANGED",
        module="users",
        details=f"User ID {user_id} role changed to {new_role}",
        ip_address=request.remote_addr
    )

    flash(f"User role updated to {new_role}", "success")
    return redirect(url_for("admin.employees.user_management"))


# ============================================================
# EDIT EMPLOYEE
# ============================================================
@bp.route("/edit/<int:emp_id>", methods=["GET", "POST"])
@login_required
@role_required("admin", "hr")
def edit_employee(emp_id):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "GET":
        cursor.execute("SELECT * FROM employees WHERE id=%s", (emp_id,))
        emp = cursor.fetchone()

        cursor.execute("SELECT * FROM departments")
        departments = cursor.fetchall()

        return render_template("employee_edit.html", emp=emp, departments=departments)

    full_name = request.form.get("full_name")
    email = request.form.get("email")
    phone = request.form.get("phone", "")
    gender = request.form.get("gender")
    job_title = request.form.get("job_title")
    department_id = request.form.get("department_id")
    join_date = request.form.get("join_date")
    status = request.form.get("status")

    # Validate email format
    from utils.validators import validate_email
    is_valid_email, email_error = validate_email(email)
    if not is_valid_email:
        flash(f"Invalid email: {email_error}", "danger")
        return redirect(url_for("employees.edit_employee", emp_id=emp_id))

    photo_file = request.files.get("photo")
    update_photo = False
    photo = None
    encoding_bytes = None

    if photo_file and photo_file.filename.strip() != "":
        # Validate file upload
        from utils.validators import validate_image_upload
        is_valid, error_msg = validate_image_upload(photo_file)
        if not is_valid:
            flash(f"Photo upload failed: {error_msg}", "danger")
            return redirect(url_for("employees.view_employee", emp_id=emp_id))
        
        update_photo = True

        folder_path = f"static/uploads/employees/{emp_id}/"
        os.makedirs(folder_path, exist_ok=True)

        filename = secure_filename(photo_file.filename)
        photo = os.path.join(folder_path, filename)
        photo_file.save(photo)

        try:
            # Use InsightFace for consistent embeddings
            img = cv2.imread(photo)
            if img is None:
                flash("Failed to read uploaded photo!", "danger")
                return redirect(url_for("employees.edit_employee", emp_id=emp_id))

            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            embedding = face_encoder.get_embedding(rgb)

            if embedding is None:
                flash("No face detected in the new photo!", "danger")
                logger.warning(f"No face detected in updated photo for employee ID: {emp_id}")
                return redirect(url_for("employees.edit_employee", emp_id=emp_id))

            embedding_bytes = embedding.astype(np.float32).tobytes()
            
            # Update face_data table
            cursor.execute("""
                INSERT INTO face_data (emp_id, embedding, image_path, created_at)
                VALUES (%s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    embedding = VALUES(embedding),
                    image_path = VALUES(image_path),
                    created_at = NOW()
            """, (emp_id, embedding_bytes, photo))
        except Exception as e:
            logger.error(f"Error processing photo for employee {emp_id}: {e}", exc_info=True)
            flash(f"Error processing photo: {str(e)}", "danger")
            return redirect(url_for("employees.edit_employee", emp_id=emp_id))

    try:
        base_update_query = """
            UPDATE employees
            SET full_name=%s, email=%s, phone=%s, gender=%s, job_title=%s,
                department_id=%s, join_date=%s, status=%s
        """
        params = [full_name, email, phone, gender, job_title, department_id, join_date, status]

        if update_photo:
            base_update_query += ", photo=%s"
            params.append(photo)

        base_update_query += " WHERE id=%s"
        params.append(emp_id)

        cursor.execute(base_update_query, tuple(params))
        db.commit()

        # Invalidate cache if photo was updated
        if update_photo:
            invalidate_embeddings_cache()

        # Audit log
        log_audit(
            user_id=session.get('user_id'),
            action='EMPLOYEE_UPDATED',
            module='employees',
            details=f'Updated employee ID: {emp_id}',
            ip_address=request.remote_addr
        )

        flash("Employee updated successfully!", "success")
        logger.info(f"Employee updated: ID {emp_id}")
        return redirect(url_for("employees.list_employees"))
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating employee {emp_id}: {e}", exc_info=True)
        flash(f"Error updating employee: {str(e)}", "danger")
        return redirect(url_for("employees.edit_employee", emp_id=emp_id))


# ============================================================
# FACE REQUESTS MANAGEMENT
# ============================================================
@bp.route("/face_requests")
@login_required
@role_required("admin", "hr")
def face_requests():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            pfr.*,
            e.full_name AS employee_name,
            e.email AS employee_email,
            u.username AS approved_by_username
        FROM pending_face_requests pfr
        JOIN employees e ON pfr.emp_id = e.id
        LEFT JOIN users u ON pfr.approved_by = u.id
        ORDER BY pfr.requested_at DESC
    """)

    requests = cursor.fetchall()

    return render_template("admin/face_requests.html", requests=requests)


@bp.route("/face_request/<int:request_id>/<action>", methods=["POST"])
@login_required
@role_required("admin", "hr")
def process_face_request(request_id, action):
    if action not in ["approve", "reject"]:
        return jsonify({"success": False, "message": "Invalid action"}), 400

    rejection_reason = request.form.get("reason", "").strip() if action == "reject" else None

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get request details
    cursor.execute("SELECT * FROM pending_face_requests WHERE id = %s", (request_id,))
    request_data = cursor.fetchone()

    if not request_data:
        return jsonify({"success": False, "message": "Request not found"}), 404

    if request_data["status"] != "pending":
        return jsonify({"success": False, "message": "Request already processed"}), 400

    try:
        if action == "approve":
            # Move image to faces folder and save to face_data
            import shutil
            from utils.face_encoder import face_encoder

            faces_folder = os.path.join("static", "faces")
            ensure_folder(faces_folder)

            # Generate new filename
            new_filename = f"{request_data['emp_id']}_{int(datetime.now().timestamp())}.jpg"
            new_path = os.path.join(faces_folder, new_filename)

            # Copy from pending to faces
            shutil.copy2(request_data["image_path"], new_path)

            # Encode face (with error logging)
            try:
                embedding = face_encoder.encode_face_from_image(new_path)
                if embedding is None:
                    logger.error(f"Failed to encode face for pending request id={request_id}, image={new_path}")
                    return jsonify({"success": False, "message": "Failed to encode face"}), 500
            except Exception as e:
                logger.error(f"Exception while encoding face for request id={request_id}: {e}", exc_info=True)
                return jsonify({"success": False, "message": "Error encoding face"}), 500

            # Save to face_data
            cursor.execute("""
                INSERT INTO face_data (emp_id, image_path, embedding)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                image_path = VALUES(image_path),
                embedding = VALUES(embedding),
                created_at = CURRENT_TIMESTAMP
            """, (request_data["emp_id"], new_path, embedding.tobytes()))

            # Update request
            cursor.execute("""
                UPDATE pending_face_requests
                SET status = 'approved', approved_at = NOW(), approved_by = %s
                WHERE id = %s
            """, (session.get("user_id"), request_id))

            # Invalidate cache
            invalidate_embeddings_cache()

        elif action == "reject":
            # Update request
            cursor.execute("""
                UPDATE pending_face_requests
                SET status = 'rejected', approved_at = NOW(), approved_by = %s, rejection_reason = %s
                WHERE id = %s
            """, (session.get("user_id"), rejection_reason, request_id))

            # Optionally delete image
            if os.path.exists(request_data["image_path"]):
                os.remove(request_data["image_path"])

        db.commit()

        # Get employee details for email (use full_name column)
        cursor.execute("SELECT full_name AS name, email FROM employees WHERE id = %s", (request_data["emp_id"],))
        employee = cursor.fetchone()

        # Send notification email to employee
        if employee and employee['email']:
            email_service = EmailService(current_app)
            if action == "approve":
                subject = "Face Enrollment Request Approved"
                body = f"""
Dear {employee['name']},

Your face {request_data['request_type']} request has been approved.

You can now use face recognition for attendance.

Best regards,
FaceTrack Team
"""
            elif action == "reject":
                subject = "Face Enrollment Request Rejected"
                reason_text = f"\nReason: {rejection_reason}" if rejection_reason else ""
                body = f"""
Dear {employee['name']},

Your face {request_data['request_type']} request has been rejected.{reason_text}

Please submit a new request if needed.

Best regards,
FaceTrack Team
"""
            email_service.send_email(employee['email'], subject, body)

        log_audit(
            user_id=session.get("user_id"),
            action=f"FACE_REQUEST_{action.upper()}",
            module="face_requests",
            details=f"Processed face request ID {request_id} for employee {request_data['emp_id']}",
            ip_address=request.remote_addr
        )

        return jsonify({"success": True, "message": f"Request {action}d successfully"})

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing face request {request_id}: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
