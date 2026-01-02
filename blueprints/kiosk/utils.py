import os
import io
import base64
from datetime import datetime
import numpy as np
from PIL import Image
import cv2
from flask import url_for, request

from insightface.app import FaceAnalysis
from db_utils import fetchall, fetchone, execute
from utils.face_encoder import face_encoder
from utils.logger import logger

from blueprints.settings.routes import load_settings

# Toggle saving snapshots globally. Default from environment variable
# Use app.config['SAVE_SNAPSHOTS'] to override at runtime (True/False)
_env_snap = os.getenv("SAVE_SNAPSHOTS", "1")
SAVE_SNAPSHOTS = str(_env_snap).lower() not in ("0", "false", "no", "off")


# -------------------------------------------------------------
# EMBEDDING CACHE (With automatic expiry/refresh)
# -------------------------------------------------------------
embeddings_cache = None
cache_timestamp = None
CACHE_TTL = 300  # 5 minutes - refresh cache to detect new enrollments


# -------------------------------------------------------------
# IMAGE HANDLING
# -------------------------------------------------------------

def decode_frame(frame_b64):
    if frame_b64.startswith("data:"):
        frame_b64 = frame_b64.split(",", 1)[1]

    img_bytes = base64.b64decode(frame_b64)
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    rgb_arr = np.array(pil_img)
    bgr_arr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)

    return pil_img, bgr_arr


def save_snapshot(img, app, filename):
    # app-level override if explicitly set
    app_override = app.config.get("SAVE_SNAPSHOTS", None)
    if app_override is not None:
        try:
            if not bool(app_override):
                return None
        except Exception:
            pass

    if not SAVE_SNAPSHOTS:
        return None  # 🔕 demo mode: no snapshots at all

    settings = load_settings()
    if settings.get("snapshot_mode", "off") != "on":
        return None

    folder = app.config.get("SNAPSHOT_DIR", "static/snapshots")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    img.save(path, "JPEG")
    return path.replace("\\", "/")


# -------------------------------------------------------------
# EMBEDDINGS DATABASE
# -------------------------------------------------------------

def load_embeddings():
    """Load face embeddings from database with automatic cache refresh.
    
    Cache expires after CACHE_TTL seconds to ensure new enrollments are recognized.
    """
    global embeddings_cache, cache_timestamp
    import time
    
    now = time.time()
    
    # Check if cache is still valid
    if embeddings_cache is not None and cache_timestamp is not None:
        age = now - cache_timestamp
        if age < CACHE_TTL:
            logger.debug(f"Using cached embeddings (age: {age:.1f}s)")
            return embeddings_cache
        else:
            logger.info(f"Cache expired ({age:.1f}s > {CACHE_TTL}s), reloading embeddings")
    
    # Cache miss or expired - reload from database
    logger.info("Loading face embeddings from database...")

    rows = fetchall("""
        SELECT
            e.id AS emp_id,
            e.full_name,
            d.name AS department,
            e.profile_photo AS photo,
            f.embedding
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        JOIN face_data f ON f.emp_id = e.id
    """)

    embeddings = []
    for row in rows:
        emb_blob = row.get("embedding")
        if not emb_blob:
            continue
        if isinstance(emb_blob, str):
            emb_blob = emb_blob.encode("latin1")
        if isinstance(emb_blob, memoryview):
            emb_blob = emb_blob.tobytes()
        if isinstance(emb_blob, bytearray):
            emb_blob = bytes(emb_blob)

        try:
            emb = np.frombuffer(emb_blob, dtype=np.float32)
            if emb.size != 512:
                raise ValueError(f"unexpected embedding size {emb.size}")
        except Exception:
            continue

        embeddings.append({
            "emp_id": row["emp_id"],
            "name": row["full_name"],
            "dept": row["department"],
            "photo": row["photo"],
            "embedding": emb
        })

    embeddings_cache = embeddings
    cache_timestamp = now  # Update cache timestamp
    logger.info(f"Loaded {len(embeddings)} face embeddings successfully")
    
    return embeddings_cache


def clear_embedding_cache():
    """
    Clears cache timestamp to force immediate reload on next access.
    Useful when new employee is enrolled or face data is updated.
    """
    global embeddings_cache, cache_timestamp
    embeddings_cache = None
    cache_timestamp = None
    logger.info("Embedding cache cleared, will reload on next access")


def reload_embeddings():
    """
    Forces immediate reload of embeddings from database.
    """
    global embeddings_cache
    embeddings_cache = None
    return load_embeddings()


# Removed duplicate matching logic - now using face_encoder.match() for consistency


# -------------------------------------------------------------
# ATTENDANCE HELPERS
# -------------------------------------------------------------

def mark_attendance(emp_id, snap_path, app=None):
    if emp_id is None:
        return {"status": "error", "message": "missing employee id"}

    now = datetime.now()
    today_date = now.date()

    previous = fetchone("""
        SELECT *
        FROM attendance
        WHERE employee_id = %s AND date = %s
        LIMIT 1
    """, (emp_id, today_date))

    if previous is None:
        execute("""
            INSERT INTO attendance (
                employee_id,
                date,
                check_in_time,
                status,
                captured_photo_path,
                timestamp
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (emp_id, today_date, now, "check-in", snap_path, now))
        return {"status": "check-in", "timestamp": now}

    # cooldown_seconds controlled by app.config['KIOSK_COOLDOWN_SECONDS'] (seconds)
    cooldown_seconds = float(app.config.get("KIOSK_COOLDOWN_SECONDS", 5)) if app else 5
    last_timestamp = previous.get("timestamp") or previous.get("check_in_time") or now

    if previous.get("status") == "check-in" and not previous.get("check_out_time"):
        if (now - last_timestamp).total_seconds() < cooldown_seconds:
            return {"status": "already", "timestamp": last_timestamp, "reason": "cooldown"}

        working_hours = None
        check_in_time = previous.get("check_in_time")
        if check_in_time:
            working_hours = (now - check_in_time).total_seconds() / 3600

        execute("""
            UPDATE attendance
            SET
                check_out_time = %s,
                working_hours = %s,
                status = %s,
                captured_photo_path = %s,
                timestamp = %s
            WHERE employee_id = %s AND date = %s
        """, (now, working_hours, "check-out", snap_path, now, emp_id, today_date))
        return {"status": "check-out", "timestamp": now, "working_hours": working_hours}

    return {"status": "already", "timestamp": last_timestamp, "reason": "already_checked_out"}


# -------------------------------------------------------------
# MAIN KIOSK FLOW
# -------------------------------------------------------------

def recognize_and_mark(frame_b64, app):
    from flask import session

    try:
        now_str = datetime.now().strftime("%I:%M %p")
        pil_img, np_img = decode_frame(frame_b64)
        
        # Use centralized face_encoder
        faces = face_encoder.app.get(np_img)
        
        # DEBUG: Log face detection
        logger.info(f"🔍 Kiosk: Detected {len(faces)} face(s) in frame")

        # Thread-safe cooldown using session (per-client)
        last_unknown_str = session.get("kiosk_last_unknown")
        unknown_cooldown = float(app.config.get("KIOSK_UNKNOWN_COOLDOWN", 3))
        now = datetime.now()

        if last_unknown_str:
            try:
                last_unknown = datetime.fromisoformat(last_unknown_str)
                if (now - last_unknown).total_seconds() < unknown_cooldown:
                    return {"status": "ignore", "recognized": False}
            except:
                pass

        if not faces:
            snap = save_snapshot(
                pil_img, app, f"unknown_{datetime.now().strftime('%H%M%S')}.jpg")
            session["kiosk_last_unknown"] = now.isoformat()
            return {
                "status": "unknown",
                "recognized": False,
                "face_detected": False,
                "name": "Unknown",
                "dept": "",
                "photoUrl": url_for("static", filename="default_user.png"),
                "time": now_str,
                "snapshot": snap
            }

        face = max(
            faces,
            key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])
        )

        embedding = face.normed_embedding.astype("float32")
        
        # Extract face box for UI feedback
        bbox = face.bbox
        face_box = {
            "x": float(bbox[0]),
            "y": float(bbox[1]),
            "width": float(bbox[2] - bbox[0]),
            "height": float(bbox[3] - bbox[1])
        }
        
        # Use centralized face_encoder.match() for consistency
        threshold = float(app.config.get("EMBED_THRESHOLD", 0.75))
        result = face_encoder.match(embedding, threshold=threshold)
        
        logger.info(f"🎯 Kiosk: Threshold={threshold}, Match result={result}")

        if result is None:
            match = None
            sim_score = 0.0
            logger.info(f"❌ Kiosk: No match found (similarity below {threshold})")
        else:
            emp_id_match, similarity = result
            sim_score = float(similarity)
            logger.info(f"✅ Kiosk: Matched employee_id={emp_id_match}, similarity={sim_score:.3f}")
            # Find full employee details from cache
            db_entries = load_embeddings()
            match = next((e for e in db_entries if e["emp_id"] == emp_id_match), None)

        x1, y1, x2, y2 = map(int, face.bbox)
        face_crop = pil_img.crop((x1, y1, x2, y2))
        snap = save_snapshot(
            face_crop, app, f"face_{datetime.now().strftime('%H%M%S')}.jpg")

        if not match:
            session["kiosk_last_unknown"] = now.isoformat()
            return {
                "status": "unknown",
                "recognized": False,
                "face_detected": True,
                "face_box": face_box,
                "name": "Unknown",
                "dept": "",
                "photoUrl": url_for("static", filename="default_user.png"),
                "time": now_str,
                "snapshot": snap,
                "similarity": float(sim_score)
            }

        emp_id = match["emp_id"]
        name = match["name"]
        dept = match["dept"]
        db_photo = match["photo"]

        if db_photo and db_photo.startswith("static/"):
            photo_url = "/" + db_photo.replace("\\", "/")
        else:
            photo_url = url_for("static", filename="default_user.png")

        attendance_result = mark_attendance(emp_id, snap, app)
        status = attendance_result.get("status", "unknown")
        display_timestamp = attendance_result.get("timestamp") or datetime.now()
        display_time = display_timestamp.strftime("%I:%M %p")

        # Audit attendance marking
        try:
            from db_utils import log_audit
            log_audit(
                user_id=emp_id,
                action="ATTENDANCE",
                module="kiosk",
                details=f"status={status} similarity={sim_score}",
                ip_address=request.remote_addr if request else None
            )
        except Exception:
            # best-effort; do not fail recognition flow on audit errors
            pass

        return {
            "status": status,
            "recognized": True,
            "face_detected": True,
            "face_box": face_box,
            "name": name,
            "dept": dept,
            "photoUrl": photo_url,
            "time": display_time,
            "snapshot": snap,
            "similarity": float(sim_score)
        }
    except Exception as e:
        logger.error(f"recognize_and_mark error: {e}", exc_info=True)
        # Ensure we always return a dictionary expected by the frontend
        return {
            "status": "WAIT",
            "recognized": False,
            "message": "Scanning..."
        }
