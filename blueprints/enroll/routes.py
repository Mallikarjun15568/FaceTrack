import os
import io
import base64
from datetime import datetime
from flask import render_template, request, jsonify, session, redirect, flash
from . import bp
from utils.db import get_db
from utils.helpers import generate_unique_filename, ensure_folder
from blueprints.auth.utils import login_required

from blueprints.kiosk import utils as kiosk_utils
from insightface.app import FaceAnalysis
import numpy as np
import cv2

# Load model once
model = FaceAnalysis(name="buffalo_l")
model.prepare(ctx_id=0, det_size=(640, 640))


# -----------------------------------------------------
# 1. Load enrollment page (New Enrollment)
# -----------------------------------------------------
@bp.route("/<int:employee_id>")
@login_required
def enroll_page(employee_id):
    # Only admin and HR can enroll faces
    if session.get("role") not in ["admin", "hr"]:
        flash("Only admins and HR can enroll faces", "error")
        return redirect("/dashboard")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM employees WHERE id = %s", (employee_id,))
    employee = cursor.fetchone()

    if not employee:
        return "Employee not found", 404

    return render_template("employees_face_enroll.html", employee=employee)


# -----------------------------------------------------
# 1B. Update Enrollment Page
# -----------------------------------------------------
@bp.route("/update/<int:employee_id>")
@login_required
def update_enroll_page(employee_id):
    # Only admin and HR can update enrollment
    if session.get("role") not in ["admin", "hr"]:
        flash("Only admins and HR can update enrollment", "error")
        return redirect("/dashboard")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM employees WHERE id = %s", (employee_id,))
    employee = cursor.fetchone()

    if not employee:
        return "Employee not found", 404

    return render_template("employees_face_enroll_update.html", employee=employee)


# -----------------------------------------------------
# 2. Capture + Save face embedding (New Enrollment)
# -----------------------------------------------------
@bp.route("/capture", methods=["POST"])
@login_required
def capture_face():
    # Only admin and HR can capture faces
    if session.get("role") not in ["admin", "hr"]:
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    try:
        data = request.get_json()
        employee_id = data.get("employee_id")
        image_base64 = data.get("image")

        if not employee_id or not image_base64:
            return jsonify({"status": "error", "message": "Invalid data"}), 400

        # Decode base64 image
        header, encoded = image_base64.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        img_np = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        # Detect face
        faces = model.get(frame)
        if len(faces) == 0:
            return jsonify({"status": "no_face", "message": "No Face Detected"})

        face = faces[0]
        embedding = face.normed_embedding.astype("float32")
        emb_bytes = embedding.astype(np.float32).tobytes()

        # Save face image
        folder_path = os.path.join("static", "faces", str(employee_id))
        ensure_folder(folder_path)

        filename = generate_unique_filename("jpg")
        file_path = os.path.join(folder_path, filename)

        with open(file_path, "wb") as f:
            f.write(img_bytes)

        # Save to DB
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM face_data WHERE emp_id = %s", (employee_id,))
        cursor.execute(
            """
            INSERT INTO face_data (emp_id, embedding, image_path, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (employee_id, emb_bytes, file_path, datetime.now())
        )
        db.commit()
        if hasattr(kiosk_utils, "reload_embeddings"):
            kiosk_utils.reload_embeddings()
        else:
            kiosk_utils.embeddings_cache = None

        return jsonify({
            "status": "success",
            "message": "Face enrolled successfully",
            "image_path": file_path
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# -----------------------------------------------------
# 2B. UPDATE EXISTING ENROLLMENT
# -----------------------------------------------------
@bp.route("/update_capture", methods=["POST"])
@login_required
def update_capture_face():
    # Only admin and HR can update captures
    if session.get("role") not in ["admin", "hr"]:
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    try:
        data = request.get_json()
        employee_id = data.get("employee_id")
        image_base64 = data.get("image")

        if not employee_id or not image_base64:
            return jsonify({"status": "error", "message": "Invalid data"}), 400

        # Decode Base64 Image
        header, encoded = image_base64.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        img_np = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        # Detect face
        faces = model.get(frame)
        if len(faces) == 0:
            return jsonify({"status": "no_face", "message": "No Face Detected"})

        face = faces[0]
        new_embedding = face.normed_embedding.astype("float32")
        new_emb_bytes = new_embedding.astype(np.float32).tobytes()

        db = get_db()
        cursor = db.cursor()

        # 1️⃣ Delete OLD embeddings
        cursor.execute("DELETE FROM face_data WHERE emp_id = %s", (employee_id,))

        # 2️⃣ Delete OLD images from folder
        folder_path = os.path.join("static", "faces", str(employee_id))
        ensure_folder(folder_path)

        for file in os.listdir(folder_path):
            try:
                os.remove(os.path.join(folder_path, file))
            except:
                pass

        # 3️⃣ Save NEW image
        filename = generate_unique_filename("jpg")
        file_path = os.path.join(folder_path, filename)

        with open(file_path, "wb") as f:
            f.write(img_bytes)

        # 4️⃣ Insert NEW embedding
        cursor.execute(
            """
            INSERT INTO face_data (emp_id, embedding, image_path, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (employee_id, new_emb_bytes, file_path, datetime.now())
        )
 
        db.commit()
        if hasattr(kiosk_utils, "reload_embeddings"):
            kiosk_utils.reload_embeddings()
        else:
            kiosk_utils.embeddings_cache = None

        return jsonify({
            "status": "success",
            "message": "Face updated successfully",
            "image_path": file_path
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# -----------------------------------------------------
# 3. Enrollment list page
# -----------------------------------------------------
@bp.route("/")
@login_required
def enroll_home():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            e.id,
            e.full_name,
            d.name AS department,

            CASE 
                WHEN fd.emp_id IS NOT NULL THEN 'Enrolled'
                ELSE 'Not Enrolled'
            END AS enroll_status

        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        LEFT JOIN face_data fd ON e.id = fd.emp_id
        ORDER BY e.id DESC
    """)

    employees = cursor.fetchall()

    return render_template("enroll_face_list.html", employees=employees)
