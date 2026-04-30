from flask import Blueprint

kiosko_bp = Blueprint("kiosko", __name__)

from . import routes  # noqa: E402,F401

