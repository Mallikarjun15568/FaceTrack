# utils/db.py
"""
Robust MySQL connection pool helpers for FaceTrack Pro.

Provides:
- initialize_pool(): create pool (lazy)
- get_connection(): get a raw connection from pool (caller must close)
- get_db(): per-request connection stored on flask.g (auto-closed by close_db)
- close_db(error=None): teardown helper for Flask appcontext

Reads DB config from environment variables (use a .env file in project root).
"""

import os
import time
import logging
from dotenv import load_dotenv
from flask import g, current_app

# mysql-connector imports
import mysql.connector
from mysql.connector import pooling, errors

load_dotenv()

logger = logging.getLogger(__name__)

# Config (read from env; avoid hard-coded secrets)
_DB_HOST = os.getenv("DB_HOST", "localhost")
_DB_USER = os.getenv("DB_USER", "root")
_DB_PASSWORD = os.getenv("DB_PASSWORD")
_DB_NAME = os.getenv("DB_NAME", "facetrack_db")
_DB_POOL_NAME = os.getenv("DB_POOL_NAME", "facetrack_pool")
_DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "8"))
_DB_POOL_RESET = os.getenv("DB_POOL_RESET_SESSION", "True").lower() in ("1", "true", "yes")
_DB_CONN_TIMEOUT = int(os.getenv("DB_CONN_TIMEOUT", "10"))
_DB_MAX_ATTEMPTS = int(os.getenv("DB_MAX_POOL_ATTEMPTS", "3"))
_DB_AUTH_PLUGIN = os.getenv("DB_AUTH_PLUGIN", None)  # e.g. "mysql_native_password"

_pool = None


def initialize_pool():
    """
    Initialize the connection pool (idempotent).
    Called lazily on first get_connection() call.
    """
    global _pool
    if _pool is not None:
        return _pool

    logger.info("Initializing MySQL connection pool: name=%s size=%s", _DB_POOL_NAME, _DB_POOL_SIZE)
    kwargs = dict(
        pool_name=_DB_POOL_NAME,
        pool_size=_DB_POOL_SIZE,
        pool_reset_session=_DB_POOL_RESET,
        host=_DB_HOST,
        user=_DB_USER,
        password=_DB_PASSWORD,
        database=_DB_NAME,
        connection_timeout=_DB_CONN_TIMEOUT,
    )

    # optionally pass auth plugin if provided
    if _DB_AUTH_PLUGIN:
        kwargs["auth_plugin"] = _DB_AUTH_PLUGIN

    try:
        _pool = pooling.MySQLConnectionPool(**kwargs)
        logger.info("MySQL connection pool created successfully.")
        return _pool
    except mysql.connector.Error as e:
        logger.exception("Failed to create MySQL connection pool: %s", e)
        raise


def get_connection():
    """
    Return a fresh connection from the pool.
    Caller is responsible for closing connection (conn.close()) when done.
    This will initialize the pool lazily.
    """
    global _pool
    if _pool is None:
        initialize_pool()

    attempts = 0
    while attempts < _DB_MAX_ATTEMPTS:
        try:
            conn = _pool.get_connection()
            # ensure autocommit off by default (consistent)
            conn.autocommit = False
            return conn
        except errors.PoolError as e:
            attempts += 1
            logger.warning("Connection pool exhausted (attempt %s/%s). Retrying...", attempts, _DB_MAX_ATTEMPTS)
            time.sleep(0.5)
        except mysql.connector.Error as e:
            logger.exception("MySQL error when getting connection: %s", e)
            raise

    raise RuntimeError("Unable to obtain database connection from pool (exhausted).")


def get_db():
    """
    Returns a request-scoped connection stored on flask.g.
    Useful inside request handlers — connection will be closed by close_db().
    """
    if "db" not in g:
        try:
            g.db = get_connection()
        except Exception:
            # don't swallow — let caller handle/report
            raise
    return g.db


def close_db(error=None):
    """
    Close the request-scoped connection (if any). Safe to call in teardown.
    This will return the connection back to pool.
    """
    conn = g.pop("db", None)
    if conn is None:
        return

    try:
        # If connection is still open and in transaction, rollback to avoid locking
        try:
            if conn.is_connected():
                # rollback any uncommitted transaction
                conn.rollback()
        except Exception:
            # ignore failure to rollback
            pass

        # close returns connection to pool when pooling is used.
        conn.close()
    except Exception as e:
        # sometimes pool internals raise when adding back; log and move on
        logger.exception("Error closing DB connection: %s", e)


# Optional small helpers for simple use-cases
def execute_fetchall(query, params=None, dict_result=True):
    """
    Convenience: execute a query and return fetchall. Connection is obtained from pool and closed.
    """
    conn = get_connection()
    cursor = None
    try:
        cursor = conn.cursor(dictionary=dict_result) if dict_result else conn.cursor()
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        return rows
    finally:
        if cursor:
            cursor.close()
        try:
            conn.close()
        except Exception as e:
            logger.exception("Error closing DB connection in execute_fetchall: %s", e)


# -------------------------
# Safe helpers
# -------------------------
def execute_query(cursor, query, params=None):
    """Execute query with error handling"""
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return True
    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        return False


def fetch_one(cursor, query, params=None):
    """Fetch single row safely"""
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchone()
    except Exception as e:
        logger.error(f"Fetch one failed: {e}", exc_info=True)
        return None


def fetch_all(cursor, query, params=None):
    """Fetch all rows safely"""
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Fetch all failed: {e}", exc_info=True)
        return []
