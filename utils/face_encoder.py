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

            self.embeddings.append(emb)
            self.employee_ids.append(row["emp_id"])

        if self.embeddings:
            self._emb_matrix = np.vstack(self.embeddings)
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

        dists = np.linalg.norm(self._emb_matrix - emb, axis=1)

        idx = int(np.argmin(dists))
        dist = float(dists[idx])

        print("🔍 Match Score:", dist)

        if dist <= threshold:
            return self.employee_ids[idx], dist

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
