import os
import io
import base64
from datetime import datetime
from flask import render_template, request, jsonify, session, redirect, flash
from . import bp
from utils.db import get_db
from utils.helpers import generate_unique_filename, ensure_folder
from blueprints.auth.utils import login_required, role_required

from blueprints.kiosk import utils as kiosk_utils
from utils.face_encoder import invalidate_embeddings_cache, face_encoder
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()
# import face_recognition  # Moved to local import to avoid startup issues

import numpy as np
import cv2
from utils.logger import logger
import logging
log = logging.getLogger(__name__)


# Duplicate face threshold for preventing same person enrolling multiple times
DUPLICATE_FACE_THRESHOLD = 0.5
# 1. Load enrollment page (New Enrollment)
# -----------------------------------------------------
@bp.route("/<int:employee_id>")
@login_required
@role_required("admin", "hr")
def enroll_page(employee_id):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM employees WHERE id = %s", (employee_id,))
    employee = cursor.fetchone()

    if not employee:
        return "Employee not found", 404

    # Determine if this employee actually has face data recorded
    cursor.execute("SELECT id, image_path FROM face_data WHERE emp_id = %s LIMIT 1", (employee_id,))
    face_row = cursor.fetchone()
    has_face = bool(face_row)

    return render_template("employees_face_enroll.html", employee=employee, has_face=has_face)


# -----------------------------------------------------
# 1B. Update Enrollment Page
# -----------------------------------------------------
@bp.route("/update/<int:employee_id>")
@login_required
@role_required("admin", "hr")
def update_enroll_page(employee_id):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            e.*,
            fd.image_path AS face_image,
            fd.created_at AS face_updated_at
        FROM employees e
        LEFT JOIN face_data fd ON fd.emp_id = e.id
        WHERE e.id = %s
    """, (employee_id,))
    employee = cursor.fetchone()

    if not employee:
        return "Employee not found", 404

    # HARD GUARD: Update page only if face exists
    if not employee.get("face_image"):
        flash("No face enrolled for this employee. Please enroll face first.", "warning")
        return redirect(f"/enroll/{employee_id}")

    return render_template("employees_face_enroll_update.html", employee=employee)


# -----------------------------------------------------
# 2. Capture + Save face embedding (New Enrollment)
# -----------------------------------------------------
@bp.route("/capture", methods=["GET", "POST"])
@login_required
@role_required("admin", "hr")
def capture_face():
    if request.method == "GET":
        return jsonify({"error": "Method not allowed"}), 405

    # CSRF protection: validate token sent in `X-CSRFToken` header
    csrf_token = request.headers.get('X-CSRFToken')
    if not csrf_token:
        return jsonify({"status": "error", "message": "Security validation failed. Please refresh the page."}), 403

    try:
        data = request.get_json()
        employee_id = data.get("employee_id")
        image_base64 = data.get("image")

        if not employee_id or not image_base64:
            return jsonify({"status": "error", "message": "Invalid data"}), 400

        # 🚨 HARD BLOCK: Check if employee already has face enrolled
        db_check = get_db()
        cursor_check = db_check.cursor(dictionary=True)
        cursor_check.execute(
            "SELECT id FROM face_data WHERE emp_id = %s LIMIT 1",
            (employee_id,)
        )
        already_enrolled = cursor_check.fetchone()
        cursor_check.close()

        if already_enrolled:
            return jsonify({
                "status": "error",
                "message": "Face already enrolled for this employee. Use update instead."
            }), 400

        # Decode image using central helper
        try:
            pil_img, frame = kiosk_utils.decode_frame(image_base64)
        except Exception:
            return jsonify({"status": "error", "message": "Invalid image format"}), 400

        # --- BLUR CHECK START ---
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Agar variance 70-80 se kam hai, matlab image dhundhli hai
        if laplacian_var < 80: 
            return jsonify({
                "status": "error", 
                "message": f"Photo bahut dhundhli (blur) hai (Quality: {laplacian_var:.1f}). Kripya saaf photo khinchein."
            }), 400
        # --- BLUR CHECK END ---

        # Save temporary image
        temp_folder = os.path.join("static", "temp")
        ensure_folder(temp_folder)
        temp_filename = generate_unique_filename("jpg")
        temp_path = os.path.join(temp_folder, temp_filename)
        try:
            pil_img.save(temp_path, "JPEG")
        except Exception:
            # fallback: write raw bytes if save fails
            with open(temp_path, "wb") as f:
                f.write(base64.b64decode(image_base64.split(',',1)[1] if ',' in image_base64 else image_base64))

        # Proceed to detect face and store embedding
        faces = face_encoder.app.get(frame)
        
        # Filter faces by minimum confidence
        from flask import current_app
        min_confidence = float(current_app.config.get("MIN_CONFIDENCE", 85)) / 100.0
        faces = [f for f in faces if getattr(f, 'det_score', 1.0) >= min_confidence]
        
        if len(faces) == 0:
            try:
                os.remove(temp_path)
            except Exception:
                pass
            return jsonify({"status": "low_confidence", "message": f"No face detected with sufficient confidence (min: {min_confidence:.0%})"})

        if len(faces) > 1:
            try:
                os.remove(temp_path)
            except Exception:
                pass
            return jsonify({
                "status": "error",
                "message": "Multiple faces detected. Only one face allowed during enrollment."
            }), 400

        face = faces[0]
        embedding = face.normed_embedding.astype("float32")

        # Check for duplicate faces across employees
        db_check = get_db()
        cursor_check = db_check.cursor(dictionary=True)
        cursor_check.execute("SELECT emp_id, embedding FROM face_data WHERE emp_id != %s", (employee_id,))
        existing_faces = cursor_check.fetchall()
        cursor_check.close()

        for face_row in existing_faces:
            existing_emb = face_encoder._decode_embedding(face_row['embedding'])
            # Compute cosine similarity (both are normalized)
            sim = np.dot(embedding, existing_emb)
            if sim >= DUPLICATE_FACE_THRESHOLD:  # Prevent duplicate enrollment
                # Log duplicate detection for audit
                user_id = session.get('user_id', 'unknown')
                log.warning(f"DUPLICATE FACE DETECTED: User {user_id} tried to enroll employee {employee_id}, matched with existing employee {face_row['emp_id']}, similarity {sim:.3f}")
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                return jsonify({"status": "duplicate", "message": f"Face already enrolled for employee ID {face_row['emp_id']}"}), 409

        emb_bytes = embedding.astype(np.float32).tobytes()

        # Save face image in per-employee folder
        folder_path = os.path.join("static", "faces", str(employee_id))
        ensure_folder(folder_path)

        filename = generate_unique_filename("jpg")
        file_path = os.path.join(folder_path, filename)
        os.replace(temp_path, file_path)

        # Save to DB
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("DELETE FROM face_data WHERE emp_id = %s", (employee_id,))
            cursor.execute(
                """
                INSERT INTO face_data (emp_id, embedding, image_path, created_at)
                VALUES (%s, %s, %s, %s)
                """,
                (employee_id, emb_bytes, file_path, datetime.now())
            )
            db.commit()
        except Exception as e:
            db.rollback()
            # Cleanup saved file on DB failure
            try:
                os.remove(file_path)
            except Exception:
                pass
            return jsonify({"status": "error", "message": f"Database error: {str(e)}"}), 500
        try:
            kiosk_utils.reload_embeddings(force=True)
        except TypeError:
            # older signature: call without force
            kiosk_utils.reload_embeddings()
        # Invalidate face-encoder cache so recognizer reloads from DB
        try:
            invalidate_embeddings_cache()
        except Exception:
            pass
        # Immediately reload face_encoder embeddings so kiosk recognizer
        # sees the new embedding without waiting for another trigger.
        try:
            face_encoder.load_all_embeddings()
        except Exception:
            pass

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
@bp.route("/update_capture", methods=["GET", "POST"])
@login_required
@role_required("admin", "hr")
def update_capture_face():
    if request.method == "GET":
        return jsonify({"error": "Method not allowed"}), 405

    # CSRF protection: validate token sent in `X-CSRFToken` header
    csrf_token = request.headers.get('X-CSRFToken')
    if not csrf_token:
        return jsonify({"status": "error", "message": "Security validation failed. Please refresh the page."}), 403

    try:
        data = request.get_json()
        employee_id = data.get("employee_id")
        image_data = data.get("image")

        if not employee_id or not image_data:
            return jsonify({
                "status": "error",
                "message": "Invalid request data"
            }), 400

        # 🚨 HARD CHECK: Face must already exist to update
        db_check = get_db()
        cursor_check = db_check.cursor(dictionary=True)
        cursor_check.execute(
            "SELECT id FROM face_data WHERE emp_id = %s LIMIT 1",
            (employee_id,)
        )
        existing_face = cursor_check.fetchone()
        cursor_check.close()

        if not existing_face:
            return jsonify({
                "status": "error",
                "message": "No existing face found for this employee. Please enroll face first."
            }), 400

        # BASE64 → BYTES
        header, encoded = image_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)

        # Decode image using central helper (same as capture_face)
        try:
            pil_img, frame = kiosk_utils.decode_frame(image_data)
        except Exception:
            return jsonify({"status": "error", "message": "Invalid image format"}), 400

        # --- BLUR CHECK START ---
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Agar variance 70-80 se kam hai, matlab image dhundhli hai
        if laplacian_var < 80: 
            return jsonify({
                "status": "error", 
                "message": f"Photo bahut dhundhli (blur) hai (Quality: {laplacian_var:.1f}). Kripya saaf photo khinchein."
            }), 400
        # --- BLUR CHECK END ---

        # Check for faces before embedding
        faces = face_encoder.app.get(frame)
        
        # Filter faces by minimum confidence
        from flask import current_app
        min_confidence = float(current_app.config.get("MIN_CONFIDENCE", 85)) / 100.0
        faces = [f for f in faces if getattr(f, 'det_score', 1.0) >= min_confidence]
        
        if len(faces) == 0:
            return jsonify({"status": "low_confidence", "message": f"No face detected with sufficient confidence (min: {min_confidence:.0%})"})

        if len(faces) > 1:
            return jsonify({
                "status": "error",
                "message": "Multiple faces detected. Only one face allowed during enrollment."
            }), 400

        face = faces[0]
        embedding = face.normed_embedding.astype("float32")

        # Check for duplicate faces across other employees
        db_check = get_db()
        cursor_check = db_check.cursor(dictionary=True)
        cursor_check.execute("SELECT emp_id, embedding FROM face_data WHERE emp_id != %s", (employee_id,))
        existing_faces = cursor_check.fetchall()
        cursor_check.close()

        for face_row in existing_faces:
            existing_emb = face_encoder._decode_embedding(face_row['embedding'])
            # Compute cosine similarity (both are normalized)
            sim = np.dot(embedding, existing_emb)
            if sim >= DUPLICATE_FACE_THRESHOLD:  # Prevent duplicate enrollment
                # Log duplicate detection for audit
                user_id = session.get('user_id', 'unknown')
                log.warning(f"DUPLICATE FACE DETECTED: User {user_id} tried to update enrollment for employee {employee_id}, matched with existing employee {face_row['emp_id']}, similarity {sim:.3f}")
                return jsonify({"status": "duplicate", "message": f"Face already enrolled for employee ID {face_row['emp_id']}"}), 409

        embedding_bytes = embedding.astype(np.float32).tobytes()

        # Save image
        folder = os.path.join("static", "faces", str(employee_id))
        ensure_folder(folder)

        filename = generate_unique_filename("jpg")
        image_path = os.path.join(folder, filename)

        with open(image_path, "wb") as f:
            f.write(img_bytes)


        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            # 1. Pehle purani image ka path fetch karein (sirf track rakhne ke liye)
            cursor.execute("SELECT image_path FROM face_data WHERE emp_id = %s", (employee_id,))
            old_face_row = cursor.fetchone()
            
            # 2. UPDATE query chalayein (Delete+Insert se behtar hai)
            # Agar record nahi hai toh ye kuch nahi karega, isliye check pehle hi kar chuke hain
            cursor.execute("""
                UPDATE face_data 
                SET embedding = %s, image_path = %s, created_at = %s 
                WHERE emp_id = %s
            """, (embedding_bytes, image_path, datetime.now(), employee_id))

            db.commit()

            # 3. COMMIT ke BAAD hi purani file delete karein
            if old_face_row and old_face_row['image_path']:
                old_path = old_face_row['image_path']
                if os.path.exists(old_path) and old_path != image_path:
                    try:
                        os.remove(old_path)
                    except Exception as e:
                        log.error(f"Old file cleanup failed: {e}")

        except Exception as e:
            db.rollback()
            # Nayi image delete karein kyunki DB update fail ho gaya
            if os.path.exists(image_path):
                os.remove(image_path)
            return jsonify({"status": "error", "message": f"Database error: {str(e)}"}), 500

        # Reload embeddings
        try:
            kiosk_utils.reload_embeddings(force=True)
        except TypeError:
            kiosk_utils.reload_embeddings()

        invalidate_embeddings_cache()

        try:
            face_encoder.load_all_embeddings()
        except Exception:
            pass

        return jsonify({
            "status": "success",
            "message": "Face updated successfully",
            "image_path": image_path
        })

    except Exception as e:
        log.error(f"Update face failed: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

# -----------------------------------------------------
# 3. Enrollment list page
# -----------------------------------------------------
@bp.route("/")
def enroll_home():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            e.id,
            e.full_name,
            e.photo,
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
