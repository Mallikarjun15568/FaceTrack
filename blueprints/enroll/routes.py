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
from utils.logger import logger
import numpy as np
import cv2
import face_recognition


# Duplicate face threshold for preventing same person enrolling multiple times
DUPLICATE_FACE_THRESHOLD = 0.75


# -----------------------------------------------------
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

    return render_template("employees_face_enroll.html", employee=employee)


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

    return render_template("employees_face_enroll_update.html", employee=employee)


# -----------------------------------------------------
# 2. Capture + Save face embedding (New Enrollment)
# -----------------------------------------------------
@bp.route("/capture", methods=["POST"])
@login_required
@role_required("admin", "hr")
def capture_face():

    try:
        data = request.get_json()
        employee_id = data.get("employee_id")
        image_base64 = data.get("image")

        if not employee_id or not image_base64:
            return jsonify({"status": "error", "message": "Invalid data"}), 400

        # Decode image using central helper
        try:
            pil_img, frame = kiosk_utils.decode_frame(image_base64)
        except Exception:
            return jsonify({"status": "error", "message": "Invalid image format"}), 400

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

        # Run image quality checks using centralized face_encoder
        try:
            is_valid, quality_score, issues = face_encoder.check_image_quality(temp_path)
        except Exception as e:
            # If quality check fails unexpectedly, remove temp and return error
            try:
                os.remove(temp_path)
            except Exception:
                pass
            return jsonify({"status": "error", "message": "Quality check failed"}), 500

        if not is_valid:
            # Cleanup and return issues
            try:
                os.remove(temp_path)
            except Exception:
                pass

            feedback = face_encoder.get_quality_feedback(issues)
            return jsonify({
                "status": "quality_failed",
                "message": "Image quality too low",
                "quality_score": round(quality_score, 2),
                "issues": issues,
                "feedback": feedback
            }), 400

        # Quality OK - proceed to detect face and store embedding
        faces = face_encoder.app.get(frame)
        if len(faces) == 0:
            try:
                os.remove(temp_path)
            except Exception:
                pass
            return jsonify({"status": "no_face", "message": "No Face Detected"})

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
                logger.warning(f"DUPLICATE FACE DETECTED: User {user_id} tried to enroll employee {employee_id}, matched with existing employee {face_row['emp_id']}, similarity {sim:.3f}")
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                return jsonify({"status": "error", "message": f"Face already enrolled for employee ID {face_row['emp_id']}"}), 400

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
            # Update enrollment flag in employees table
            cursor.execute("UPDATE employees SET face_enrolled = 1 WHERE id = %s", (employee_id,))
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
# 2C. FACE DETECTION (for real-time green square)
# -----------------------------------------------------
@bp.route("/detect_face", methods=["POST"])
@login_required
def detect_face():
    """
    Detect if a face is present in the image for real-time UI feedback.
    Returns: {"face_detected": true/false}
    """
    try:
        data = request.get_json()
        image_base64 = data.get("image")
        
        if not image_base64:
            return jsonify({"face_detected": False})
        
        # Decode base64 image
        image_data = base64.b64decode(image_base64.split(",")[1])
        np_arr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({"face_detected": False})
        
        # Convert BGR to RGB
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        face_locations = face_recognition.face_locations(rgb, model="hog")
        face_count = len(face_locations)
        return jsonify({
            "face_detected": face_count > 0,
            "face_count": face_count
        })
    except Exception as e:
        logger.error(f"Face detection error: {e}")
        return jsonify({"face_detected": False, "face_count": 0})


# -----------------------------------------------------
# 2B. UPDATE EXISTING ENROLLMENT
# -----------------------------------------------------
@bp.route("/update_capture", methods=["POST"])
@login_required
@role_required("admin", "hr")
def update_capture_face():
    try:
        data = request.get_json()
        employee_id = data.get("employee_id")
        image_data = data.get("image")

        if not employee_id or not image_data:
            return jsonify({
                "status": "error",
                "message": "Invalid request data"
            }), 400

        # BASE64 → BYTES
        header, encoded = image_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)

        # bytes → numpy → image
        img_array = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({
                "status": "error",
                "message": "Failed to decode image"
            }), 400

        # BGR → RGB
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Check for faces before embedding
        faces_check = face_encoder.app.get(rgb)
        if len(faces_check) == 0:
            return jsonify({
                "status": "error",
                "message": "No face detected"
            }), 400

        if len(faces_check) > 1:
            return jsonify({
                "status": "error",
                "message": "Multiple faces detected. Only one face allowed during enrollment."
            }), 400

        embedding = face_encoder.get_embedding(rgb)

        if embedding is None:
            return jsonify({
                "status": "error",
                "message": "No face detected"
            }), 400

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
                logger.warning(f"DUPLICATE FACE DETECTED: User {user_id} tried to update enrollment for employee {employee_id}, matched with existing employee {face_row['emp_id']}, similarity {sim:.3f}")
                return jsonify({"status": "error", "message": f"Face already enrolled for employee ID {face_row['emp_id']}"}), 400

        embedding_bytes = embedding.astype(np.float32).tobytes()

        # Save image
        folder = os.path.join("static", "faces", str(employee_id))
        ensure_folder(folder)

        filename = generate_unique_filename("jpg")
        image_path = os.path.join(folder, filename)

        with open(image_path, "wb") as f:
            f.write(img_bytes)


        db = get_db()
        cursor = db.cursor()

        try:
            # Always delete old face_data for this employee to prevent duplicates
            cursor.execute("DELETE FROM face_data WHERE emp_id = %s", (employee_id,))

            cursor.execute("""
    INSERT INTO face_data (emp_id, embedding, image_path, created_at)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        embedding = VALUES(embedding),
        image_path = VALUES(image_path),
        created_at = VALUES(created_at)
    """, (employee_id, embedding_bytes, image_path, datetime.now()))

            db.commit()
            # Update enrollment flag in employees table
            cursor.execute("UPDATE employees SET face_enrolled = 1 WHERE id = %s", (employee_id,))
            db.commit()
        except Exception as e:
            db.rollback()
            # Cleanup saved file on DB failure
            try:
                os.remove(image_path)
            except Exception:
                pass
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
        logger.error(f"Update face failed: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

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
