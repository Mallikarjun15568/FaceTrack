from flask import Blueprint
from blueprints.admin import check_employee

bp = Blueprint('employee', __name__, url_prefix='/employee')

bp.before_request(check_employee)

from . import routes