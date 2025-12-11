from flask import Blueprint

bp = Blueprint("attendance", __name__, url_prefix="/attendance")

from . import routes
