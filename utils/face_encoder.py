import numpy as np
import ast
from insightface.app import FaceAnalysis
from utils.db import get_db

class FaceEncoder:
    def __init__(self):
        print("[*] Loading InsightFace Model...")
        self.app = FaceAnalysis(name="buffalo_l")
        self.app.prepare(ctx_id=0, det_size=(640, 640))
        print("[+] InsightFace Ready")

        self.embeddings = []
        self.employee_ids = []
        self._emb_matrix = np.empty((0, 512), dtype=np.float32)

    # ----------------------------------------------------
    # LOAD EMBEDDINGS
    # ----------------------------------------------------
    def load_all_embeddings(self):
        print("[*] Loading All Face Embeddings...")

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
                print("[!] Failed to parse embedding:", exc)
                continue

            if emb.shape != (512,):
                print("[!] Skipping embedding with unexpected size", emb.shape)
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

        print(f"[+] Loaded {len(self.embeddings)} embeddings")


    # ----------------------------------------------------
    # GET FACE EMBEDDING
    # ----------------------------------------------------
    def get_embedding(self, frame_rgb):
        faces = self.app.get(frame_rgb)
        if not faces:
            return None

        face = faces[0]

        emb = getattr(face, "normed_embedding", None)

        return emb


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

        print("🔍 Match Score:", best_sim)

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
        print("🔄 Face embeddings cache invalidated")
    except Exception:
        pass
