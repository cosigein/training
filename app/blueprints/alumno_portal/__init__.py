from flask import Blueprint

alumno_bp = Blueprint('alumno', __name__)

from . import routes
