from flask import render_template, abort
from flask_jwt_extended import get_jwt_identity
from app.models.auth import User
from app.utils.decorators import require_role
from .student_service import get_student_dashboard, get_student_intento
from . import student_bp


def _get_org(user):
    return user.organizationId


@student_bp.route("/", methods=["GET"])
@require_role(["STUDENT"])
def dashboard():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    inscripciones = get_student_dashboard(user_id, _get_org(user))
    return render_template(
        "student/dashboard.html",
        user=user,
        inscripciones=inscripciones,
        active_page="dashboard",
    )


@student_bp.route("/intento/<string:attempt_id>", methods=["GET"])
@require_role(["STUDENT"])
def intento_detalle(attempt_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    intento = get_student_intento(attempt_id, user_id, _get_org(user))
    if not intento:
        abort(404)
    return render_template(
        "student/intento.html",
        user=user,
        intento=intento,
        active_page="dashboard",
    )
