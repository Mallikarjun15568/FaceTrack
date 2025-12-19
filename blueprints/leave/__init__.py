from flask import Blueprint

bp = Blueprint("leave", __name__, url_prefix="/leave")

from . import routes
