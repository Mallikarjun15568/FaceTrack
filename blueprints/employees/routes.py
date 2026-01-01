from . import bp
from flask import (
    render_template, request, redirect,
    url_for, flash, session, jsonify
)
import os
import cv2
import numpy as np
from werkzeug.utils import secure_filename
from utils.db import get_db
from blueprints.auth.utils import login_required
from utils.face_encoder import face_encoder, invalidate_embeddings_cache
from utils.logger import logger
from db_utils import log_audit


# ============================================================
# EMPLOYEE LIST PAGE
# ============================================================
@bp.route("/", methods=["GET"])
@login_required
def list_employees():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    page = int(request.args.get("page", 1))
    per_page = 10
    offset = (page - 1) * per_page

    department_id = request.args.get("department_id")
    enrolled = request.args.get("enrolled")
    sort = request.args.get("sort", "newest")

    where_clauses = []
    params = []

    if department_id:
        where_clauses.append("e.department_id = %s")
        params.append(department_id)

    if enrolled == "enrolled":
        where_clauses.append("fd.embedding IS NOT NULL")
    elif enrolled == "not_enrolled":
        where_clauses.append("fd.embedding IS NULL")

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # Update total count query to include face_data join
    count_query = "SELECT COUNT(*) AS total FROM employees e LEFT JOIN face_data fd ON fd.emp_id = e.id " + where_sql
    cursor.execute(count_query, tuple(params))
    total = cursor.fetchone()["total"]

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
        page=page,
        per_page=per_page,
        start=offset,
        end=offset + len(employees),
        querystring=qs,
        sort=sort
    )


# ============================================================
# ADD EMPLOYEE
# ============================================================
@bp.route("/add", methods=["GET", "POST"])
@login_required
def add_employee():
    # Only admin and HR can add employees
    if session.get("role") not in ["admin", "hr"]:
        flash("Only admins and HR can add employees", "error")
        return redirect(url_for("employees.list_employees"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "GET":
        cursor.execute("SELECT * FROM departments")
        departments = cursor.fetchall()
        return render_template("add_employee.html", departments=departments)

    full_name = request.form.get("full_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    gender = request.form.get("gender")
    department_id = request.form.get("department_id")
    job_title = request.form.get("job_title")
    join_date = request.form.get("joining_date")
    status = request.form.get("status")

    photo_file = request.files.get("photo")

    if not photo_file:
        flash("Please upload a photo!", "danger")
        return redirect(url_for("employees.add_employee"))
    
    # Validate file upload
    from utils.validators import validate_image_upload
    is_valid, error_msg = validate_image_upload(photo_file)
    if not is_valid:
        flash(f"Photo upload failed: {error_msg}", "danger")
        return redirect(url_for("employees.add_employee"))

    cursor.execute("""
        INSERT INTO employees (full_name, email, phone, gender, job_title, department_id, join_date, status, photo_path, face_embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, '', NULL)
    """, (full_name, email, phone, gender, job_title, department_id, join_date, status))
    db.commit()

    employee_id = cursor.lastrowid

    folder_path = f"static/uploads/employees/{employee_id}/"
    os.makedirs(folder_path, exist_ok=True)

    filename = secure_filename(photo_file.filename)
    image_path = os.path.join(folder_path, filename)
    photo_file.save(image_path)

    try:
        # Use InsightFace for consistent embeddings
        img = cv2.imread(image_path)
        if img is None:
            flash("Failed to read uploaded photo!", "danger")
            return redirect(url_for("employees.add_employee"))

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        embedding = face_encoder.get_embedding(rgb)

        if embedding is None:
            flash("No face detected in the photo!", "danger")
            logger.warning(f"No face detected in uploaded photo for employee: {full_name}")
            return redirect(url_for("employees.add_employee"))

        # Store embedding in face_data table (512-dim float32)
        embedding_bytes = embedding.astype(np.float32).tobytes()
        
        # Update employee photo path
        cursor.execute("""
            UPDATE employees
            SET photo_path=%s
            WHERE id=%s
        """, (image_path, employee_id))
        
        # Insert into face_data table
        cursor.execute("""
            INSERT INTO face_data (emp_id, embedding, image_path, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (employee_id, embedding_bytes, image_path))
        
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
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding employee: {e}", exc_info=True)
        flash(f"Error adding employee: {str(e)}", "danger")
        return redirect(url_for("employees.add_employee"))


# ============================================================
# DELETE EMPLOYEE
# ============================================================
@bp.route("/delete/<int:emp_id>", methods=["POST"])
@login_required
def delete_employee(emp_id):
    # Only admin and HR can delete employees
    if session.get("role") not in ["admin", "hr"]:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT photo_path FROM employees WHERE id=%s", (emp_id,))
    row = cursor.fetchone()

    cursor.execute("DELETE FROM employees WHERE id=%s", (emp_id,))
    db.commit()

    if row and row.get("photo_path") and os.path.exists(row["photo_path"]):
        os.remove(row["photo_path"])

    return jsonify({"success": True})


# ============================================================
# BULK DELETE
# ============================================================
@bp.route("/bulk_delete", methods=["POST"])
@login_required
def bulk_delete():
    # Only admin and HR can bulk delete
    if session.get("role") not in ["admin", "hr"]:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.get_json()
    ids = data.get("ids", [])

    if not ids:
        return jsonify({"success": False, "error": "No IDs provided"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    placeholders = ",".join(["%s"] * len(ids))
    query = "DELETE FROM employees WHERE id IN (" + placeholders + ")"
    cursor.execute(query, tuple(ids))
    db.commit()

    return jsonify({"success": True})


# ============================================================
# VIEW EMPLOYEE
# ============================================================
@bp.route("/view/<int:emp_id>")
@login_required
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
# EDIT EMPLOYEE
# ============================================================
@bp.route("/edit/<int:emp_id>", methods=["GET", "POST"])
@login_required
def edit_employee(emp_id):
    # Only admin and HR can edit employees
    if session.get("role") not in ["admin", "hr"]:
        flash("Only admins and HR can edit employees", "error")
        return redirect(url_for("employees.list_employees"))

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
    phone = request.form.get("phone")
    gender = request.form.get("gender")
    job_title = request.form.get("job_title")
    department_id = request.form.get("department_id")
    join_date = request.form.get("join_date")
    status = request.form.get("status")

    photo_file = request.files.get("photo")
    update_photo = False
    photo_path = None
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
        photo_path = os.path.join(folder_path, filename)
        photo_file.save(photo_path)

        try:
            # Use InsightFace for consistent embeddings
            img = cv2.imread(photo_path)
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
            """, (emp_id, embedding_bytes, photo_path))
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
            base_update_query += ", photo_path=%s"
            params.append(photo_path)

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
