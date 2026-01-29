import mysql.connector
from mysql.connector import pooling, errors
import logging
from werkzeug.security import generate_password_hash, check_password_hash
import time
from flask import g
from config import Config  # Use Config class from config.py for DB values

logger = logging.getLogger('db_utils')

# -------------------------------
# DATABASE CONFIG (from config.py)
# -------------------------------
db_config = {
    'host': Config.DB_HOST,
    'user': Config.DB_USER,
    'password': Config.DB_PASSWORD,
    'database': Config.DB_NAME,
    'connection_timeout': 10,
}

pool_config = {
    'pool_name': 'mypool',
    'pool_size': 10,
    'pool_reset_session': True,
}

MAX_POOL_ATTEMPTS = 3

connection_pool = None


# -------------------------------------------
# CREATE CONNECTION POOL (ONCE)
# -------------------------------------------
def initialize_pool():
    global connection_pool

    if connection_pool is None:
        try:
            logger.info("Creating MySQL connection pool (name=%s, size=%s)",
                        pool_config['pool_name'], pool_config['pool_size'])

            connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name=pool_config['pool_name'],
                pool_size=pool_config['pool_size'],
                pool_reset_session=pool_config['pool_reset_session'],
                **db_config
            )

            logger.info("Connection pool created successfully")

        except mysql.connector.Error as e:
            logger.exception("Failed to create connection pool: %s", e)
            raise RuntimeError(f"Could not create connection pool: {e}")


# -------------------------------------------
# GET CONNECTION FROM POOL (SAFE)
# -------------------------------------------
def get_connection():
    global connection_pool

    if connection_pool is None:
        initialize_pool()

    attempts = 0
    while attempts < MAX_POOL_ATTEMPTS:
        try:
            return connection_pool.get_connection()

        except errors.PoolError:
            attempts += 1
            logger.warning("Pool exhausted, attempt %s/%s", attempts, MAX_POOL_ATTEMPTS)
            time.sleep(1)

    raise RuntimeError("MySQL connection pool exhausted.")


# -------------------------------------------
# FLASK g-CONTEXT CONNECTION
# -------------------------------------------
def get_db():
    if "db" not in g:
        g.db = get_connection()
    return g.db


# -------------------------------------------
# AUTO-CLOSE DB AFTER EACH REQUEST
# -------------------------------------------
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
        except Exception as e:
            logger.exception("Error closing DB connection: %s", e)


# -------------------------------------------
# USER HELPERS
# -------------------------------------------
def user_exists(username):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def create_user(username, password, role='employee'):
    conn = get_db()
    cursor = conn.cursor()
    try:
        hashed = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
        """, (username, hashed, role))
        conn.commit()
    finally:
        cursor.close()


def validate_user(username, password):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        return row and check_password_hash(row['password'], password)
    finally:
        cursor.close()

# -------------------------------------------
# GENERIC QUERY HELPERS (Required by kiosk)
# -------------------------------------------

def fetchall(query, params=None):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()


def fetchone(query, params=None):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()


def execute(query, params=None):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()


# -------------------------------------------
# SETTINGS HELPERS
# -------------------------------------------
def get_setting(key, default=None):
    """Retrieve a setting value from the settings table."""
    try:
        row = fetchone("SELECT setting_value FROM settings WHERE setting_key = %s", (key,))
        return row["setting_value"] if row else default
    except Exception as e:
        logger.error(f"Error fetching setting {key}: {e}")
        return default


def set_setting(key, value):
    """Insert or update a setting in the settings table."""
    try:
        existing = fetchone("SELECT id FROM settings WHERE setting_key = %s", (key,))
        if existing:
            execute(
                "UPDATE settings SET setting_value = %s WHERE setting_key = %s",
                (value, key)
            )
        else:
            execute(
                "INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s)",
                (key, value)
            )
        return True
    except Exception as e:
        logger.error(f"Error setting {key}: {e}")
        logger.exception(e)
        return False


def log_audit(user_id, action, module=None, details=None, ip_address=None):
    """Insert a row into audit_logs table. Safe wrapper to record audit events.

    The `audit_logs` table schema contains `user_id`, `action`, `details`, and
    an auto-populated `timestamp`. Avoid inserting non-existent columns.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO audit_logs (user_id, action, details)
            VALUES (%s, %s, %s)
            """,
            (user_id, action, details)
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}", exc_info=True)
        return False
