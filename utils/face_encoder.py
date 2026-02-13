import numpy as np
import ast
from insightface.app import FaceAnalysis
from utils.db import get_db
from utils.logger import logger
import cv2


class FaceEncoder:
    def __init__(self):
        try:
            logger.info("[*] Loading InsightFace Model...")
            self.app = FaceAnalysis(name="buffalo_l")
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            logger.info("[+] InsightFace Ready")
        except Exception as e:
            logger.error(f"Failed to initialize FaceAnalysis model: {e}", exc_info=True)
            raise

        self.embeddings = []
        self.employee_ids = []
        self._emb_matrix = np.empty((0, 512), dtype=np.float32)

    # ----------------------------------------------------
    # LOAD EMBEDDINGS
    # ----------------------------------------------------
    def load_all_embeddings(self):
        logger.info("Loading all face embeddings from database...")

        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT emp_id, embedding FROM face_data")
        rows = cur.fetchall()
        cur.close()

        self.embeddings = []
        self.employee_ids = []

        for row in rows:
            emb_blob = row.get("embedding")
            if emb_blob is None:
                continue
            
            try:
                emb = self._decode_embedding(emb_blob)
            except Exception as exc:
                logger.warning(f"Failed to parse embedding for emp_id {row.get('emp_id')}: {exc}")
                continue

            if emb.shape != (512,):
                logger.warning(f"Skipping embedding with unexpected size {emb.shape} for emp_id {row.get('emp_id')}")
                continue

            # Normalize embedding to unit length to allow cosine similarity
            try:
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb.astype(np.float32) / float(norm)
                else:
                    emb = emb.astype(np.float32)
            except Exception:
                emb = emb.astype(np.float32)

            self.embeddings.append(emb)
            self.employee_ids.append(row["emp_id"])

        if self.embeddings:
            # Stack normalized embeddings as rows
            self._emb_matrix = np.vstack(self.embeddings).astype(np.float32)
        else:
            self._emb_matrix = np.empty((0, 512), dtype=np.float32)

        logger.info(f"[+] Loaded {len(self.embeddings)} embeddings")


    # ----------------------------------------------------
    # GET FACE EMBEDDING
    # ----------------------------------------------------
    def get_embedding(self, frame_rgb):
        try:
            faces = self.app.get(frame_rgb)
        except Exception as e:
            logger.error(f"Face detection error in get_embedding: {e}", exc_info=True)
            return None

        # Require exactly one face for a reliable embedding
        if not faces:
            return None

        if len(faces) != 1:
            logger.warning(f"get_embedding(): expected 1 face, found {len(faces)}")
            return None

        face = faces[0]
        emb = getattr(face, "normed_embedding", None)
        return emb

    def encode_face_from_image(self, image_path):
        """
        Encode face from image file path.
        Returns normalized embedding or None if encoding fails.
        """
        try:
            # Load image using OpenCV
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Failed to load image from path: {image_path}")
                return None
            
            # Convert BGR to RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Get embedding
            return self.get_embedding(img_rgb)
            
        except Exception as e:
            logger.error(f"Error encoding face from image {image_path}: {e}", exc_info=True)
            return None

    def get_quality_feedback(self, issues):
        """Convert technical issues to user-friendly feedback"""
        feedback = []
        for i in issues:
            if "Resolution" in i:
                feedback.append("Please provide a larger photo (higher resolution).")
            elif "dark" in i.lower():
                feedback.append("Photo is too dark — please take it in better lighting.")
            elif "bright" in i.lower() or "overexposed" in i.lower():
                feedback.append("Photo is too bright — avoid strong backlight.")
            elif "blurr" in i.lower():
                feedback.append("Photo appears blurry — hold the camera steady.")
            elif "multiple faces" in i.lower() or "multiple face" in i.lower():
                feedback.append("Multiple people detected — use a photo with only the subject.")
            elif "no face" in i.lower():
                feedback.append("No face detected — make sure the face is fully visible.")
            elif "too small" in i.lower():
                feedback.append("Face is too small in the frame — move closer to the camera.")
            else:
                feedback.append(i)

        return feedback


    def check_image_quality(self, image_path):
        """
        Check if image is suitable for face enrollment.
        Returns: (is_valid: bool, quality_score: float, issues: list[str])
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return False, 0.0, ["Failed to read image"]

            issues = []
            quality_score = 100.0

            # 1. Check resolution
            height, width = img.shape[:2]
            min_resolution = 200
            if width < min_resolution or height < min_resolution:
                issues.append(f"Resolution too low ({width}x{height}). Minimum: {min_resolution}x{min_resolution}")
                quality_score -= 30

            # 2. Brightness check
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            brightness = float(gray.mean())
            if brightness < 50:
                issues.append("Image too dark")
                quality_score -= 20
            elif brightness > 200:
                issues.append("Image too bright (overexposed)")
                quality_score -= 15

            # 3. Blur check (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_threshold = 100
            if laplacian_var < blur_threshold:
                issues.append(f"Image too blurry (score: {laplacian_var:.2f})")
                quality_score -= 25

            # Prepare RGB frame for face detector
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # 4. Face detection
            faces = []
            try:
                faces = self.app.get(rgb)
            except Exception as e:
                logger.error(f"Face detection during quality check failed: {e}", exc_info=True)

            if not faces:
                issues.append("No face detected")
                return False, 0.0, issues
            if len(faces) > 1:
                issues.append(f"Multiple faces detected ({len(faces)})")
                quality_score -= 20

            # 5. Face size and pose checks (use first face)
            face = faces[0]
            bbox = getattr(face, 'bbox', None)
            if bbox is not None:
                try:
                    bbox = bbox.astype(int)
                    face_width = bbox[2] - bbox[0]
                    face_height = bbox[3] - bbox[1]
                    min_face_size = 80
                    if face_width < min_face_size or face_height < min_face_size:
                        issues.append(f"Face too small ({face_width}x{face_height})")
                        quality_score -= 20
                except Exception as e:
                    logger.exception("Error processing bbox in quality check: %s", e)

            # 6. Pose check if available
            pose = getattr(face, 'pose', None)
            if pose is not None:
                try:
                    pitch = float(pose[0])
                    yaw = float(pose[1])
                    if abs(pitch) > 30 or abs(yaw) > 30:
                        issues.append("Face not front-facing")
                        quality_score -= 15
                except Exception as e:
                    logger.exception("Error processing pose in quality check: %s", e)

            # 7. Landmarks visibility
            landmarks = getattr(face, 'landmark_2d_106', None)
            if landmarks is None or (hasattr(landmarks, 'shape') and getattr(landmarks, 'shape')[0] < 5):
                issues.append("Facial landmarks not detected properly")
                quality_score -= 10

            quality_score = max(0, quality_score)
            is_valid = quality_score >= 60.0 and not any('No face detected' in s for s in issues)

            logger.info(f"Image quality check: score={quality_score:.2f}, valid={is_valid}")
            if issues:
                logger.warning(f"Quality issues: {', '.join(issues)}")

            return is_valid, quality_score, issues

        except Exception as e:
            logger.error(f"Quality check error: {e}", exc_info=True)
            return False, 0.0, [f"Quality check failed: {str(e)}"]


    # ----------------------------------------------------
    # MATCH (STRICT + RELIABLE)
    # ----------------------------------------------------
    def match(self, emb, threshold=None):
        # Use centralized threshold from config
        if threshold is None:
            from flask import current_app
            try:
                threshold = float(current_app.config.get("EMBED_THRESHOLD", 0.75))
            except:
                threshold = 0.75  # Fallback
        
        if self._emb_matrix.size == 0:
            return None

        # Ensure incoming embedding is normalized
        try:
            emb_arr = np.asarray(emb, dtype=np.float32)
            nrm = np.linalg.norm(emb_arr)
            if nrm > 0:
                emb_arr = emb_arr / float(nrm)
        except Exception:
            emb_arr = np.asarray(emb, dtype=np.float32)

        # Compute cosine similarities (dot product since vectors are normalized)
        sims = np.dot(self._emb_matrix, emb_arr)
        idx = int(np.argmax(sims))
        best_sim = float(sims[idx])

        logger.debug(f"Match score: {best_sim}")

        # For cosine similarity, higher is better. Threshold is interpreted as minimum similarity.
        if threshold is None:
            from flask import current_app
            try:
                threshold = float(current_app.config.get("EMBED_THRESHOLD", 0.75))
            except:
                threshold = 0.75

        if best_sim >= threshold:
            return self.employee_ids[idx], best_sim

        return None


    def _decode_embedding(self, emb_blob):
        if isinstance(emb_blob, memoryview):
            emb_blob = emb_blob.tobytes()
        if isinstance(emb_blob, bytearray):
            emb_blob = bytes(emb_blob)

        if isinstance(emb_blob, str):
            parsed = ast.literal_eval(emb_blob)
            return np.array(parsed, dtype=np.float32)

        if isinstance(emb_blob, (bytes,)):
            return np.frombuffer(emb_blob, dtype=np.float32)

        if isinstance(emb_blob, np.ndarray):
            return emb_blob.astype(np.float32)

        raise TypeError(f"Unsupported embedding type {type(emb_blob)}")



face_encoder = FaceEncoder()


def clear_embeddings_cache():
    """Clear the in-memory embeddings stored on the face_encoder instance.

    This is used after enrollment/update operations so that future
    recognition calls will reload embeddings from the database.
    """
    global face_encoder
    try:
        face_encoder.embeddings = []
        face_encoder.employee_ids = []
        face_encoder._emb_matrix = np.empty((0, 512), dtype=np.float32)
    except Exception:
        # best-effort; do not raise in production flow
        pass


def invalidate_embeddings_cache():
    """Invalidate the face embeddings cache (production-ready helper).

    Clears in-memory embeddings on the `face_encoder` instance so that
    subsequent recognition operations will reload embeddings from the DB.
    """
    global face_encoder
    try:
        face_encoder.embeddings = []
        face_encoder.employee_ids = []
        face_encoder._emb_matrix = np.empty((0, 512), dtype=np.float32)
        logger.info("Face embeddings cache invalidated")
    except Exception:
        pass
