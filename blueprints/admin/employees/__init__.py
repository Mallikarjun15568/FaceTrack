from flask import Blueprint

bp = Blueprint("employees", __name__)

from .. import check_admin
bp.before_request(check_admin)

from . import routes
