from flask import Blueprint

bp = Blueprint("kiosk", __name__, url_prefix="/kiosk", template_folder="templates")

from blueprints.admin import check_admin
bp.before_request(check_admin)

from . import routes
