from flask import render_template, request, redirect, url_for, abort
from flask_jwt_extended import get_jwt_identity

from app.models.auth import User
from app.utils.decorators import require_role
from .student_service import (
    get_student_dashboard,
    get_student_intento,
    get_student_historial,
    get_student_evolucion,
    get_solicitar_auditoria_ctx,
    submit_audit_request,
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
    ctx = get_student_dashboard(user.id, user.organizationId)
    if not ctx:
        return render_template("student/sin_inscripciones.html", user=user)
    return render_template(
        "student/dashboard.html",
        active_page="dashboard",
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
    auditoria_solicitada = request.args.get("auditoria") == "solicitada"
    return render_template(
        "student/intento.html",
        active_page="dashboard",
        is_subpage=True,
        auditoria_solicitada=auditoria_solicitada,
        **ctx,
    )


@student_bp.route("/intento/<string:attempt_id>/auditoria", methods=["GET"])
@require_role(["STUDENT"])
def solicitar_auditoria(attempt_id):
    user = _current_user()
    ctx = get_solicitar_auditoria_ctx(attempt_id, user.id, user.organizationId)
    if not ctx:
        abort(404)
    if ctx.get("existing"):
        return redirect(url_for("student.intento", attempt_id=attempt_id))

    razon = (request.args.get("razon") or "").strip()
    error = None

    if razon:
        try:
            submit_audit_request(attempt_id, user.id, user.organizationId, razon)
            return redirect(
                url_for("student.intento", attempt_id=attempt_id, auditoria="solicitada")
            )
        except ValueError as exc:
            error = str(exc)

    return render_template(
        "student/solicitar_auditoria.html",
        active_page="dashboard",
        is_subpage=True,
        razon_previa=razon,
        error=error,
        **{k: v for k, v in ctx.items() if k != "existing"},
    )
