import uuid
import os
import time

def generate_unique_filename(extension="jpg"):
    return f"{uuid.uuid4().hex}.{extension}"

def ensure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        
def ensure_folder(path):
    os.makedirs(path, exist_ok=True)

def generate_unique_filename(ext="jpg"):
    return f"{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"