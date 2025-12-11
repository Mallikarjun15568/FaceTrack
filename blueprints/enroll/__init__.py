from flask import Blueprint

bp = Blueprint("enroll", __name__, url_prefix="/enroll")

from . import routes
