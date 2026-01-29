from flask import Blueprint
from blueprints.admin import check_admin_hr

bp = Blueprint("attendance", __name__, url_prefix="/attendance")

bp.before_request(check_admin_hr)

from . import routes
