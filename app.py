from flask import Flask, render_template, redirect, url_for, flash, session, jsonify, send_from_directory
import logging
import time
import os
from dotenv import load_dotenv

from config import SECRET_KEY
from db_utils import get_connection, close_db
from utils.face_encoder import face_encoder

# --------------------------
# BLUEPRINT IMPORTS
# --------------------------
from blueprints.auth import bp as auth_bp
from blueprints.employees import bp as employees_bp
from blueprints.attendance import bp as attendance_bp
from blueprints.enroll import bp as enroll_bp
from blueprints.kiosk import bp as kiosk_bp
from blueprints.dashboard import bp as dashboard_bp
from blueprints.settings import bp as settings_bp
from blueprints.reports import bp as reports_bp
from blueprints.leave import bp as leave_bp
from blueprints.charts import bp as charts_bp
from utils.email_service import email_service


# --------------------------
# FLASK APP SETUP
# --------------------------
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Secure session configuration
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 hour


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

# ==========================
# EMAIL (SYSTEM EMAIL CONFIG) - load from environment (.env)
# ==========================
app.config['SMTP_SERVER'] = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
app.config['SMTP_PORT'] = int(os.getenv('SMTP_PORT', 587))
app.config['SENDER_EMAIL'] = os.getenv('SENDER_EMAIL')
app.config['SENDER_PASSWORD'] = os.getenv('SENDER_PASSWORD')
app.config['SENDER_NAME'] = os.getenv('SENDER_NAME', 'FaceTrack Pro')

# init email service (loads SMTP config from app.config)
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
app.register_blueprint(employees_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(enroll_bp)
app.register_blueprint(kiosk_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(leave_bp)
app.register_blueprint(charts_bp)


# --------------------------
# ROOT ROUTES
# --------------------------
@app.route("/")
def index():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/favicon.ico", endpoint="favicon")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static", "images"),
        "facetrack_pro.png",
        mimetype="image/png"
    )


# --------------------------
# LOGIN REDIRECT
# --------------------------
@app.route("/login")
def login_redirect():
    return redirect(url_for("auth.login"))


# --------------------------
# DB HEALTH CHECK
# --------------------------
@app.route("/db-health")
def db_health():
    start = time.time()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()

        latency = int((time.time() - start) * 1000)
        return jsonify({"status": "ok", "latency_ms": latency}), 200
    except Exception as e:
        logger.exception("DB health check failed")
        return jsonify({"status": "error", "message": str(e)}), 500


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
    print("[*] Loading face embeddings from DB...")
    face_encoder.load_all_embeddings()
    print("[+] Embeddings loaded successfully!")


# --------------------------
# RUN SERVER
# --------------------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
