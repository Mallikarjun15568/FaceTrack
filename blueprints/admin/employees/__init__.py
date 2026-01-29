from flask import Blueprint

bp = Blueprint("employees", __name__)

# Individual routes handle their own role checks with @role_required("admin", "hr")
from . import routes
