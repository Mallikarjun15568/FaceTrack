from flask import Blueprint

bp = Blueprint("dashboard", __name__)

from .. import check_admin
bp.before_request(check_admin)

from . import routes
