from flask import Flask, render_template, redirect, url_for, flash, session, jsonify, send_from_directory, request, abort
import logging
import time
import os
from dotenv import load_dotenv
from utils.extensions import limiter
from flask_wtf.csrf import CSRFProtect, generate_csrf

from config import Config
from db_utils import get_connection, close_db, get_setting
from utils.logger import logger
import shutil
import tempfile
from utils.face_encoder import face_encoder

# --------------------------
# BLUEPRINT IMPORTS
# --------------------------
from blueprints.auth import bp as auth_bp
from blueprints.admin import admin_bp
from blueprints.attendance import bp as attendance_bp
from blueprints.enroll import bp as enroll_bp
from blueprints.kiosk import bp as kiosk_bp
from blueprints.admin.settings.routes import load_settings
from blueprints.leave import bp as leave_bp
from blueprints.charts import bp as charts_bp
from utils.email_service import email_service


# --------------------------
# FLASK APP SETUP
# --------------------------
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config.get('SECRET_KEY')

# Initialize database connection pool FIRST
from db_utils import initialize_pool
try:
    logger.info("Initializing MySQL connection pool...")
    initialize_pool()
    logger.info("Database connection pool initialized successfully")
except Exception as e:
    logger.critical(f"Failed to initialize database connection pool: {e}", exc_info=True)
    raise RuntimeError("Cannot start application without database connection")

# Initialize CSRF for templates (settings page uses csrf_token())
csrf = CSRFProtect(app)

# expose csrf on the app object so blueprints can safely call "state.app.csrf"
app.csrf = csrf

limiter.init_app(app)

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# Ensure global access as well (fallback for templates)
app.jinja_env.globals['csrf_token'] = generate_csrf

# Secure session configuration
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# Set secure cookie flag in production
app.config["SESSION_COOKIE_SECURE"] = app.config.get('APP_MODE', 'development') == 'production'
# Lifetime in seconds
app.config["PERMANENT_SESSION_LIFETIME"] = int(os.getenv('PERMANENT_SESSION_LIFETIME', 3600))  # 1 hour


# --------------------------
# UPLOAD FOLDER
# --------------------------
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Kiosk settings
app.config["KIOSK_COOLDOWN_SECONDS"] = float(os.getenv("KIOSK_COOLDOWN_SECONDS", "5"))
app.config["KIOSK_UNKNOWN_COOLDOWN"] = float(os.getenv("KIOSK_UNKNOWN_COOLDOWN", "3"))
app.config["EMBED_THRESHOLD"] = float(os.getenv("EMBED_THRESHOLD", "0.75"))

load_dotenv()

# Check for local FontAwesome bundle and expose flag to templates to avoid client-side 404s
fa_local_path = os.path.join(app.root_path, 'static', 'vendor', 'fontawesome', 'css', 'all.min.css')
app.config['FA_LOCAL_AVAILABLE'] = os.path.exists(fa_local_path)

@app.context_processor
def inject_feature_flags():
    return dict(FA_LOCAL_AVAILABLE=app.config.get('FA_LOCAL_AVAILABLE', False))

# ==========================
# EMAIL (SYSTEM EMAIL CONFIG) - load from environment (.env)
# ==========================
app.config['SMTP_SERVER'] = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
app.config['SMTP_PORT'] = int(os.getenv('SMTP_PORT', 587))
app.config['SENDER_EMAIL'] = os.getenv('SENDER_EMAIL')
app.config['SENDER_PASSWORD'] = os.getenv('SENDER_PASSWORD')
app.config['SENDER_NAME'] = os.getenv('SENDER_NAME', 'FaceTrack Pro')

# Initialize email service with app config
email_service.init_app(app)


# --------------------------
# LOGGING SETUP
# --------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("app")


# --------------------------
# REGISTER BLUEPRINTS
# 
# --------------------------
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(enroll_bp)
app.register_blueprint(kiosk_bp)
app.register_blueprint(leave_bp)
app.register_blueprint(charts_bp)
from blueprints.employee import bp as employee_bp
app.register_blueprint(employee_bp)

# Setup selective CSRF exemptions
from utils.csrf_exemptions import setup_csrf_exemptions
setup_csrf_exemptions(app, csrf)


# --------------------------
# ROOT ROUTES
# --------------------------
@app.route("/")
def index():
    # If user already logged in → go to their panel
    if session.get("user_id"):
        role = session.get("role")
        if role == "employee" and session.get("employee_id"):
            return redirect(url_for("employee.dashboard"))
        elif role in ["admin", "hr"]:
            return redirect(url_for("admin.dashboard.admin_dashboard"))
        # Fallback for other roles or incomplete profiles
        return redirect(url_for("auth.login"))
    # Not logged in → show public home page
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # CSRF check
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(request.form.get('csrf_token'))
        except Exception as e:
            flash("CSRF token validation failed", "error")
            return redirect(url_for("contact"))
        
        # Handle contact form submission
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        
        # Basic validation
        if not name or not email or not message:
            flash("All fields are required", "error")
            return redirect(url_for("contact"))
        
        # Email validation
        from utils.validators import validate_email
        is_valid, error_msg = validate_email(email)
        if not is_valid:
            flash("Invalid email format", "error")
            return redirect(url_for("contact"))
        
        # Store contact message in database
        try:
            from db_utils import execute

            # Insert into database
            execute("""
                INSERT INTO contact_messages (name, email, message)
                VALUES (%s, %s, %s)
            """, (name, email, message))

            flash("Thank you for your message! We'll get back to you soon.", "success")

        except Exception as e:
            from utils.logger import logger
            logger.error(f"Failed to save contact form message: {e}")
            flash("Sorry, there was an error saving your message. Please try again later.", "error")
        
        return redirect(url_for("contact"))
    
    return render_template("contact.html")

@app.route("/help")
def help_page():
    return render_template("help.html")


@app.route("/favicon.ico", endpoint="favicon")
def favicon():
    # Serve only the static/favicon.ico file. This project relies solely on that file.
    static_dir = os.path.join(app.root_path, "static")
    favicon_path = os.path.join(static_dir, "favicon.ico")
    if os.path.exists(favicon_path):
        return send_from_directory(static_dir, "favicon.ico", mimetype="image/x-icon")
    # If missing, return 404 so issues are visible during development
    abort(404)


# --------------------------
# LOGIN REDIRECT
# --------------------------
@app.route("/login")
def login_redirect():
    return redirect(url_for("auth.login"))


# --------------------------
# ERROR HANDLERS
# --------------------------
@app.errorhandler(403)
def forbidden(error):
    logger.warning(f"403 Forbidden: {request.url} - {str(error)}")
    return render_template('403.html'), 403


@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 Error: {request.url}")
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Error: {str(error)}", exc_info=True)
    try:
        # attempt to rollback any open DB transaction
        close_db()
    except Exception:
        pass
    return render_template('500.html'), 500


@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    try:
        close_db()
    except Exception:
        pass
    return jsonify({'error': 'Internal server error', 'message': 'Something went wrong. Please try again.'}), 500


# DB health and deep health endpoints removed per user request.


# --------------------------
# APP TEARDOWN
# --------------------------
@app.teardown_appcontext
def teardown_db(exception):
    close_db()


# --------------------------
# LOAD FACE EMBEDDINGS AT STARTUP
# --------------------------
with app.app_context():
    # --- Startup: sync persistent settings from DB into runtime config ---
    try:
        saved_settings = load_settings()
        if saved_settings:
            # Recognition threshold
            try:
                if 'recognition_threshold' in saved_settings:
                    app.config['EMBED_THRESHOLD'] = float(saved_settings.get('recognition_threshold'))
            except Exception:
                pass

            # Duplicate attendance interval (minutes) -> cooldown seconds
            try:
                if 'duplicate_interval' in saved_settings:
                    mins = float(saved_settings.get('duplicate_interval'))
                    app.config['KIOSK_COOLDOWN_SECONDS'] = mins * 60.0
            except Exception:
                pass

            # Snapshot mode
            try:
                if 'snapshot_mode' in saved_settings:
                    app.config['SAVE_SNAPSHOTS'] = str(saved_settings.get('snapshot_mode')).lower() == 'on'
            except Exception:
                pass

            # Minimum confidence
            try:
                if 'min_confidence' in saved_settings:
                    app.config['MIN_CONFIDENCE'] = float(saved_settings.get('min_confidence'))
            except Exception:
                pass

            # Camera index
            try:
                if 'camera_index' in saved_settings:
                    app.config['DEFAULT_CAMERA_INDEX'] = int(saved_settings.get('camera_index'))
            except Exception:
                pass

            # Session timeout (minutes)
            try:
                if 'session_timeout' in saved_settings:
                    app.config['PERMANENT_SESSION_LIFETIME'] = int(saved_settings.get('session_timeout')) * 60
            except Exception:
                pass

            # Misc mirrors
            try:
                if 'login_alert' in saved_settings:
                    app.config['LOGIN_ALERT'] = saved_settings.get('login_alert')
                if 'company_name' in saved_settings:
                    app.config['COMPANY_NAME'] = saved_settings.get('company_name')
                if 'company_logo' in saved_settings:
                    app.config['COMPANY_LOGO'] = saved_settings.get('company_logo')
                if 'late_time' in saved_settings:
                    app.config['LATE_TIME'] = saved_settings.get('late_time')
                # Company check-out time (HH:MM)
                if 'checkout_time' in saved_settings:
                    app.config['CHECKOUT_TIME'] = saved_settings.get('checkout_time')
            except Exception:
                pass

    except Exception as e:
        logger.exception("Failed to sync settings from DB at startup: %s", e)

    logger.info("Loading face embeddings from database...")
    try:
        face_encoder.load_all_embeddings()
        logger.info(f"Successfully loaded {len(face_encoder.embeddings)} face embeddings")
    except Exception as e:
        logger.error(f"Failed to load face embeddings: {e}", exc_info=True)
        logger.warning("Application will start but face recognition may not work properly")


# --------------------------
# RUN SERVER
# --------------------------
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("FaceTrack Application Starting...")
    logger.info(f"Environment: {app.config.get('APP_MODE', 'development')}")
    logger.info(f"Debug Mode: {app.config.get('DEBUG', False)}")
    logger.info("=" * 50)

    debug_mode = bool(app.config.get('DEBUG', False))
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.getenv('PORT', 5000)), use_reloader=False)

