from flask import Blueprint

mobile_api_bp = Blueprint("mobile_api", __name__, url_prefix="/api/v1")

from app.blueprints.mobile_api import routes, errors  # noqa: E402, F401
