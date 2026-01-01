"""
Thread-safe face encoder wrapper with mutex lock
"""
import threading
import numpy as np
from utils.face_encoder import face_encoder as _face_encoder

class ThreadSafeFaceEncoder:
    """Thread-safe wrapper for face_encoder with lock protection"""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._encoder = _face_encoder
    
    def load_all_embeddings(self):
        """Thread-safe embedding loading"""
        with self._lock:
            return self._encoder.load_all_embeddings()
    
    def get_embedding(self, frame_rgb):
        """Thread-safe embedding extraction"""
        # InsightFace model is thread-safe for read operations
        return self._encoder.get_embedding(frame_rgb)
    
    def match(self, emb, threshold=None):
        """Thread-safe embedding matching"""
        with self._lock:
            return self._encoder.match(emb, threshold)
    
    def check_image_quality(self, image_path):
        """Thread-safe image quality check"""
        return self._encoder.check_image_quality(image_path)
    
    @property
    def embeddings(self):
        """Thread-safe access to embeddings list"""
        with self._lock:
            return self._encoder.embeddings.copy() if self._encoder.embeddings else []
    
    @property
    def app(self):
        """Direct access to InsightFace app (read-only operations are thread-safe)"""
        return self._encoder.app

# Export thread-safe instance
thread_safe_encoder = ThreadSafeFaceEncoder()
