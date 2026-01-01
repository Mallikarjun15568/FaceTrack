import os
from dotenv import load_dotenv
import warnings

# Load .env file at startup (if present)
load_dotenv()


class BaseConfig:
    """Base configuration with common settings"""
    
    # --- SECURITY ---
    # CRITICAL: SECRET_KEY must be set in .env, no fallback!
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in environment variables! Add it to .env file.")
    
    # --- DATABASE SETTINGS ---
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME", "facetrack_db")
    
    if not DB_PASSWORD:
        warnings.warn("DB_PASSWORD not set! Database connection will fail.")
    
    # --- FACE RECOGNITION SETTINGS ---
    RECOGNITION_THRESHOLD = float(os.getenv("RECOGNITION_THRESHOLD", "1.1"))
    RECOGNITION_PROVIDER = os.getenv("RECOGNITION_PROVIDER", "CPU")
    EMBED_THRESHOLD = float(os.getenv("EMBED_THRESHOLD", "0.75"))
    
    # --- APP SETTINGS ---
    APP_MODE = os.getenv("APP_MODE", "development")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # --- UPLOAD SETTINGS ---
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(5 * 1024 * 1024)))  # 5MB default
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # --- SESSION SETTINGS ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', '3600'))  # 1 hour
    
    # --- KIOSK SETTINGS ---
    KIOSK_COOLDOWN_SECONDS = float(os.getenv("KIOSK_COOLDOWN_SECONDS", "5"))
    KIOSK_UNKNOWN_COOLDOWN = float(os.getenv("KIOSK_UNKNOWN_COOLDOWN", "3"))
    
    # --- EMAIL SETTINGS ---
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
    SENDER_NAME = os.getenv('SENDER_NAME', 'FaceTrack Pro')
    
    # --- PAGINATION ---
    ITEMS_PER_PAGE = 10
    
    # --- RATE LIMITING ---
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    
    # Production should have stricter settings
    if not os.getenv('SENDER_EMAIL'):
        warnings.warn("SENDER_EMAIL not configured for production!")


class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    DB_NAME = "facetrack_test_db"


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

# Get active configuration based on APP_MODE
Config = config_map.get(os.getenv('APP_MODE', 'development'), DevelopmentConfig)

# Configuration validation
if Config.DEBUG:
    print(f"[Config] Loaded configuration: {Config.__name__}")
    print(f"[Config] Database: {Config.DB_NAME}")
    print(f"[Config] Debug Mode: {Config.DEBUG}")
