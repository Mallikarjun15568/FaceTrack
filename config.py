import os
from dotenv import load_dotenv

# Load .env file at startup
load_dotenv()

# --- SECURITY ---
SECRET_KEY = os.getenv("SECRET_KEY")

# --- DATABASE SETTINGS ---
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

# --- FACE RECOGNITION SETTINGS ---
RECOGNITION_THRESHOLD = float(os.getenv("RECOGNITION_THRESHOLD", 1.1))
RECOGNITION_PROVIDER = os.getenv("RECOGNITION_PROVIDER", "CPU")
EMBED_THRESHOLD = float(os.getenv("EMBED_THRESHOLD", 0.75))  # Centralized threshold for all recognition modules

# --- APP SETTINGS ---
APP_MODE = os.getenv("APP_MODE", "development")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
