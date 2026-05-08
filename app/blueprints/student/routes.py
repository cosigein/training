from flask import render_template, request, redirect, url_for, abort
from flask_jwt_extended import get_jwt_identity

from app.models.auth import User
from app.utils.decorators import require_role
from .student_service import (
    get_student_dashboard,
    get_student_intento,
    get_student_historial,
    get_student_evolucion,
    get_active_enrollments_summary,
)
from . import student_bp


def _current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id) if user_id else None


@student_bp.route("/", methods=["GET"])
@student_bp.route("/dashboard", methods=["GET"])
@require_role(["STUDENT"])
def dashboard():
    user = _current_user()
    conv_id = request.args.get("conv_id")

    convocatorias_activas = get_active_enrollments_summary(user.id, user.organizationId)
    if not conv_id and convocatorias_activas:
        conv_id = convocatorias_activas[0]["conv_id"]

    ctx = get_student_dashboard(user.id, user.organizationId, conv_id)
    if not ctx:
        return render_template("student/sin_inscripciones.html", user=user)
    return render_template(
        "student/dashboard.html",
        active_page="dashboard",
        convocatorias_activas=convocatorias_activas,
        **ctx,
    )


@student_bp.route("/historial", methods=["GET"])
@require_role(["STUDENT"])
def historial():
    user = _current_user()
    ctx = get_student_historial(user.id, user.organizationId)
    if not ctx:
        return render_template("student/sin_inscripciones.html", user=user)
    return render_template(
        "student/historial.html",
        active_page="historial",
        **ctx,
    )


@student_bp.route("/evolucion", methods=["GET"])
@require_role(["STUDENT"])
def evolucion():
    user = _current_user()
    ctx = get_student_evolucion(user.id, user.organizationId)
    if not ctx:
        return render_template("student/sin_inscripciones.html", user=user)
    return render_template(
        "student/evolucion.html",
        active_page="evolucion",
        **ctx,
    )


@student_bp.route("/intento/<string:attempt_id>", methods=["GET"])
@require_role(["STUDENT"])
def intento(attempt_id):
    user = _current_user()
    ctx = get_student_intento(attempt_id, user.id, user.organizationId)
    if not ctx:
        abort(404)
    return render_template(
        "student/intento.html",
        active_page="dashboard",
        is_subpage=True,
        **ctx,
    )
