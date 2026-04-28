from flask import Blueprint

auth_bp = Blueprint("auth", __name__, template_folder="templates")

from . import routes  # Este archivo lo crearemos en la Fase 2
