from flask import Blueprint

kpis_bp = Blueprint("kpis", __name__, template_folder="templates")

from . import routes
