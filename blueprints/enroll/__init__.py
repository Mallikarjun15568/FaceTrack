from flask import Blueprint

bp = Blueprint("enroll", __name__, url_prefix="/enroll")

from blueprints.admin import check_admin_hr
bp.before_request(check_admin_hr)

from . import routes
