from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize limiter without app (init_app will be called from app.py)
limiter = Limiter(key_func=get_remote_address)
