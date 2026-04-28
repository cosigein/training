from flask import Blueprint

uploads_bp = Blueprint("uploads", __name__, template_folder="templates")

from . import routes
