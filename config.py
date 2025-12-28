import os
from dotenv import load_dotenv
import warnings

# Load .env file at startup (if present)
load_dotenv()


class Config:
	# --- SECURITY ---
	SECRET_KEY = os.getenv("SECRET_KEY") or os.urandom(24)

	# --- DATABASE SETTINGS ---
	DB_HOST = os.getenv("DB_HOST", "localhost")
	DB_USER = os.getenv("DB_USER", "root")
	DB_PASSWORD = os.getenv("DB_PASSWORD")
	DB_NAME = os.getenv("DB_NAME", "facetrack_db")

	# --- FACE RECOGNITION SETTINGS ---
	RECOGNITION_THRESHOLD = float(os.getenv("RECOGNITION_THRESHOLD", 1.1))
	RECOGNITION_PROVIDER = os.getenv("RECOGNITION_PROVIDER", "CPU")
	EMBED_THRESHOLD = float(os.getenv("EMBED_THRESHOLD", 0.75))

	# --- APP SETTINGS ---
	APP_MODE = os.getenv("APP_MODE", "development")
	DEBUG = os.getenv("DEBUG", "False").lower() == "true"

	# Uploads
	UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads")
	MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 5 * 1024 * 1024))


if not os.getenv("SECRET_KEY"):
	warnings.warn("SECRET_KEY not set in environment; a random key will be used. Set SECRET_KEY in .env for production.")

if not os.getenv("DB_PASSWORD"):
	warnings.warn("DB_PASSWORD not set in environment. Database connection may fail until DB_PASSWORD is provided.")
