from flask import Blueprint

geofences_bp = Blueprint("geofences", __name__, template_folder="templates")

from . import routes
