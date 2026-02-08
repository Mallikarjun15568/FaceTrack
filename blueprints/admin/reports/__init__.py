from flask import Blueprint

bp = Blueprint("reports", __name__)

from .. import check_admin_hr
bp.before_request(check_admin_hr)

from . import routes
