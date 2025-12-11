from flask import Blueprint

bp = Blueprint("kiosk", __name__, url_prefix="/kiosk", template_folder="templates")

from . import routes
