from flask import Blueprint

bp = Blueprint("charts", __name__, url_prefix="/charts")

from . import routes
