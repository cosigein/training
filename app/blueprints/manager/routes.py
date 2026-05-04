"""Manager portal — vistas para MANAGER y ADMIN.

Lee de la BD real (queries SQLAlchemy) vía `ranking_service` y `audit_service`.
"""
from datetime import datetime
from flask import render_template, request, abort, redirect, url_for, flash, jsonify

from app.extensions import db
from app.models.auth import User
from app.models.session import Attempt, AttemptStatus
from app.models.vehicle import Vehicle
from app.models.training import (
    Enrollment,
    TrainingAuditLog,
    AuditAction,
)
from .ranking_service import (
    get_convocatorias,
    get_first_conv_id,
    get_ranking,
    get_matrix_data,
    get_alumno_active_conv_id,
    get_alumno_detail,
    get_intento_detail,
)
from .audit_service import (
    list_audit_requests,
    get_audit_request,
    update_audit_request,
    create_audit_request,
    count_pending,
    AuditRequestError,
)
from flask_jwt_extended import get_jwt_identity
from app.utils.decorators import require_role
from . import manager_bp

def _get_org_id():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user.organizationId if user else None


def _resolve_conv_id(org_id):
    conv_id = request.args.get("conv_id")
    if conv_id:
        return conv_id
    return get_first_conv_id(org_id)


def _load_convocatorias_dicts():
    return get_convocatorias(_get_org_id())


def _load_auditorias_pendientes():
    raw = list_audit_requests(_get_org_id(), status="PENDING")
    result = []
    for ar in raw:
        fecha_hora = ar.get("createdAt", "")
        parts = fecha_hora.split(" ")
        attempt = ar.get("attempt") or {}
        result.append({
            "id": ar["id"],
            "attempt_id": attempt.get("id", ""),
            "candidato": ar.get("requester", "—"),
            "ruta": attempt.get("routeId", "—"),
            "nota": attempt.get("score") or 0,
            "fecha_solicitud": parts[0] if parts else "—",
            "hora_solicitud": parts[1] if len(parts) > 1 else "—",
            "status": ar.get("status", "PENDING"),
        })
    return result


# ── CONTEXT PROCESSOR ──────────────────────────────────────────────────────

@manager_bp.context_processor
def inject_auditorias_count():
    count = sum(1 for a in AUDITORIAS if a.get("status") == "PENDING")
    return {"auditorias_count": count}


# ── RUTAS ──────────────────────────────────────────────────────────────────

@manager_bp.route("/")
@require_role(["MANAGER", "ADMIN"])
def dashboard():
    convocatorias = _load_convocatorias_dicts()
    auditorias = _load_auditorias_pendientes()
    return render_template(
        "manager/dashboard.html",
        active_page="dashboard",
        convocatorias=convocatorias,
        auditorias=auditorias,
        pendientes_total=len(auditorias),
    )


@manager_bp.route("/convocatorias")
@require_role(["MANAGER", "ADMIN"])
def convocatorias():
    org_id = _get_org_id()
    return render_template(
        "manager/convocatorias.html",
        active_page="convocatorias",
        convocatorias=get_convocatorias(org_id),
    )


@manager_bp.route("/ranking")
@require_role(["MANAGER", "ADMIN"])
def ranking():
    org_id = _get_org_id()
    conv_id = _resolve_conv_id(org_id)
    if not conv_id:
        return render_template(
            "manager/ranking.html",
            active_page="ranking",
            convocatorias=[],
            convocatoria=None,
            ranking=[],
            plazas=0,
            nota_corte=None,
            total_candidatos=0,
        )

    conv_dict, entries = get_ranking(conv_id, org_id)
    if not conv_dict:
        abort(404)

    plazas = conv_dict["plazas"]
    nota_corte = entries[plazas - 1]["nota_media"] if len(entries) >= plazas else None

    return render_template(
        "manager/ranking.html",
        active_page="ranking",
        convocatorias=get_convocatorias(org_id),
        convocatoria=conv_dict,
        ranking=entries,
        plazas=plazas,
        nota_corte=nota_corte,
        total_candidatos=conv_dict["total_candidatos"],
    )


@manager_bp.route("/matriz")
@require_role(["MANAGER", "ADMIN"])
def matriz():
    org_id = _get_org_id()
    conv_id = _resolve_conv_id(org_id)
    if not conv_id:
        return render_template(
            "manager/matriz.html",
            active_page="matriz",
            convocatorias=[],
            convocatoria=None,
            candidatos=[],
            circuitos=[],
        )

    conv_dict, candidatos, circuitos = get_matrix_data(conv_id, org_id)
    if not conv_dict:
        abort(404)

    return render_template(
        "manager/matriz.html",
        active_page="matriz",
        convocatorias=get_convocatorias(org_id),
        convocatoria=conv_dict,
        candidatos=candidatos,
        circuitos=circuitos,
    )


@manager_bp.route("/alumno/<candidato_id>")
@require_role(["MANAGER", "ADMIN"])
def alumno_detalle(candidato_id):
    org_id = _get_org_id()
    conv_id = request.args.get("conv_id") or get_alumno_active_conv_id(candidato_id, org_id)
    if not conv_id:
        abort(404)

    conv_dict, candidato, intentos, nota_media = get_alumno_detail(candidato_id, conv_id, org_id)
    if not candidato:
        abort(404)

    return render_template(
        "manager/alumno.html",
        active_page="matriz",
        is_subpage=True,
        convocatoria=conv_dict,
        candidato=candidato,
        intentos=intentos,
        nota_media=nota_media,
    )


@manager_bp.route("/intento/<attempt_id>")
@require_role(["MANAGER", "ADMIN"])
def intento_detalle(attempt_id):
    org_id = _get_org_id()
    detail = get_intento_detail(attempt_id, org_id)
    if not detail:
        abort(404)

    attempt = Attempt.query.filter_by(id=attempt_id, organizationId=org_id).first()
    can_score = (
        attempt is not None
        and attempt.closedAt is None
        and attempt.status in (AttemptStatus.OPEN, AttemptStatus.PROCESSING)
    )

    return render_template(
        "manager/intento.html",
        active_page="matriz",
        is_subpage=True,
        candidato=detail["candidato"],
        ruta=detail["ruta"],
        nota_info=detail["nota_info"],
        attempt_id=detail["attempt_id"],
        score_breakdown=detail["score_breakdown"],
        eventos=detail["eventos"],
        auditoria=detail["auditoria"],
        convocatoria=detail["convocatoria"],
        can_score=can_score,
    )


@manager_bp.route("/intento/<attempt_id>/upload-sensor", methods=["POST"])
@require_role(["ADMIN"])
def upload_sensor_data(attempt_id):
    """Recibe el TXT del Doback Elite, parsea las mediciones y corre el pipeline completo."""
    from app.services.pipeline.sensor_parser import parse_sensor_file
    from app.services.pipeline import run_pipeline

    org_id = _get_org_id()
    attempt = Attempt.query.filter_by(id=attempt_id, organizationId=org_id).first()
    if not attempt:
        abort(404)

    redirect_url = url_for("manager.intento_detalle", attempt_id=attempt_id)

    if attempt.closedAt:
        flash("Este intento ya está cerrado.", "warning")
        return redirect(redirect_url)

    f = request.files.get("sensor_file")
    if not f or not f.filename:
        flash("No se seleccionó ningún archivo.", "danger")
        return redirect(redirect_url)

    if not f.filename.lower().endswith(".txt"):
        flash("Solo se aceptan archivos .txt del sensor Doback.", "danger")
        return redirect(redirect_url)

    try:
        content = f.read().decode("utf-8", errors="replace")
    except Exception as exc:
        flash(f"Error al leer el archivo: {exc}", "danger")
        return redirect(redirect_url)

    actor_id = get_jwt_identity()

    try:
        parse_result = parse_sensor_file(content, attempt_id, org_id)
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(redirect_url)
    except Exception as exc:
        flash(f"Error al parsear el archivo: {exc}", "danger")
        return redirect(redirect_url)

    if parse_result.total_rows == 0:
        flash("El archivo no contenía datos válidos (sin GPS fix ni datos de estabilidad).", "warning")
        return redirect(redirect_url)

    try:
        pipeline_result = run_pipeline(attempt_id, actor_id=actor_id)
        flash(
            f"Datos cargados: {parse_result.summary()}. "
            f"Score: {pipeline_result['score']} · {pipeline_result['events_detected']} eventos detectados.",
            "success",
        )
    except ValueError as exc:
        flash(f"Datos cargados ({parse_result.total_rows} filas) pero error al calcular score: {exc}", "warning")
    except Exception as exc:
        flash(f"Datos cargados ({parse_result.total_rows} filas) pero error en el pipeline: {exc}", "danger")

    return redirect(redirect_url)


@manager_bp.route("/intento/<attempt_id>/score", methods=["POST"])
@require_role(["ADMIN"])
def score_attempt(attempt_id):
    """Dispara el pipeline detect → score → cierre para un attempt OPEN."""
    from app.services.pipeline import run_pipeline

    org_id = _get_org_id()
    attempt = Attempt.query.filter_by(id=attempt_id, organizationId=org_id).first()
    if not attempt:
        abort(404)

    if attempt.closedAt:
        flash("Este intento ya está cerrado y no puede re-procesarse.", "warning")
        return redirect(url_for("manager.intento_detalle", attempt_id=attempt_id))

    actor_id = get_jwt_identity()
    try:
        result = run_pipeline(attempt_id, actor_id=actor_id)
        flash(
            f"Score calculado: {result['score']} · {result['events_detected']} eventos detectados.",
            "success",
        )
    except ValueError as e:
        flash(str(e), "warning")
    except Exception as e:
        flash(f"Error al procesar el intento: {e}", "danger")

    return redirect(url_for("manager.intento_detalle", attempt_id=attempt_id))


@manager_bp.route("/alumno/<student_id>/intento/nuevo", methods=["POST"])
@require_role(["ADMIN"])
def registrar_intento(student_id):
    """Registra un intento con nota manual para un alumno (entrada directa sin telemetría)."""
    org_id = _get_org_id()
    conv_id = request.form.get("conv_id") or request.args.get("conv_id")
    route_id = request.form.get("route_id", "").strip().upper()
    score_str = request.form.get("score", "")

    redirect_url = url_for("manager.alumno_detalle", candidato_id=student_id, conv_id=conv_id)

    try:
        score = float(score_str)
        if not (0.0 <= score <= 10.0):
            raise ValueError()
    except ValueError:
        flash("Nota inválida — debe ser un número entre 0 y 10.", "danger")
        return redirect(redirect_url)

    if not route_id:
        flash("Debe indicar el identificador de la ruta.", "danger")
        return redirect(redirect_url)

    enrollment = Enrollment.query.filter_by(
        studentId=student_id, convocatoriaId=conv_id, organizationId=org_id
    ).first()
    if not enrollment:
        flash("El alumno no está inscripto en esa convocatoria.", "warning")
        return redirect(redirect_url)

    vehicle = Vehicle.query.filter_by(organizationId=org_id).first()
    if not vehicle:
        flash("No hay vehículos registrados. Creá uno antes de ingresar notas.", "warning")
        return redirect(redirect_url)

    conv = enrollment.convocatoria
    pesos = (conv.pesosPorFamilia or {}) if conv else {}
    if not pesos:
        pesos = {"estabilidad": 0.40, "velocidad": 0.30, "ruta": 0.15, "conduccion": 0.15}
    breakdown = {fam: round(score * peso, 1) for fam, peso in pesos.items()}

    attempt_count = Attempt.query.filter_by(enrollmentId=enrollment.id).count()
    now = datetime.utcnow()

    attempt = Attempt(
        organizationId=org_id,
        vehicleId=vehicle.id,
        enrollmentId=enrollment.id,
        convocatoriaId=conv_id,
        studentId=student_id,
        routeId=route_id,
        source="manual_entry",
        status=AttemptStatus.CLOSED,
        startTime=now,
        endTime=now,
        closedAt=now,
        score=score,
        scoreRaw=score,
        scoreBreakdown=breakdown,
        criteriaVersionPinned=conv.criteriaVersion if conv else "manual",
        normalizerVersionPinned=conv.normalizerVersion if conv else "manual",
        detectorVersionPinned=conv.detectorVersion if conv else "manual",
        sequence=attempt_count + 1,
        sessionNumber=attempt_count + 1,
        attemptNumber=attempt_count + 1,
        uploadedById=get_jwt_identity(),
        dataQuality={"confidenceScore": 1.0, "source": "manual_entry"},
    )
    db.session.add(attempt)
    db.session.flush()  # obtiene attempt.id antes del commit

    enrollment.attemptsCount = (enrollment.attemptsCount or 0) + 1

    db.session.add(TrainingAuditLog(
        actorId=get_jwt_identity(),
        actorRole="ADMIN",
        action=AuditAction.ATTEMPT_CREATED,
        resourceType="Attempt",
        resourceId=attempt.id,
        delta={"score": score, "route_id": route_id, "source": "manual_entry"},
        organizationId=org_id,
    ))

    db.session.commit()

    flash(f"Nota {score:.1f} registrada para la ruta {route_id}.", "success")
    return redirect(redirect_url)


@manager_bp.route("/auditoria/<audit_id>")
@require_role(["MANAGER", "ADMIN"])
def auditoria_detalle(audit_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    ar = get_audit_request(audit_id, user.organizationId)
    if not ar:
        return jsonify({"message": "Auditoría no encontrada"}), 404
    if request.is_json:
        return jsonify(ar), 200
    return render_template("manager/auditoria_detalle.html", auditoria=ar, active_page="auditorias")


@manager_bp.route("/auditoria", methods=["GET"])
@require_role(["MANAGER", "ADMIN"])
def auditoria_list():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    status_filter = request.args.get("status")
    auditorias = list_audit_requests(user.organizationId, status=status_filter)
    if request.is_json:
        return jsonify(auditorias), 200
    return render_template(
        "manager/auditorias.html",
        auditorias=auditorias,
        active_page="auditorias",
        pendientes_total=count_pending(user.organizationId),
    )


@manager_bp.route("/auditoria/<audit_id>", methods=["PATCH"])
@require_role(["MANAGER", "ADMIN"])
def auditoria_update(audit_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json() or {}
    new_status = data.get("status", "")
    resolution = data.get("resolution", "")
    try:
        ar = update_audit_request(audit_id, user.organizationId, user_id, new_status, resolution)
    except AuditRequestError as exc:
        return jsonify({"message": str(exc)}), 422
    return jsonify(ar), 200


@manager_bp.route("/auditoria", methods=["POST"])
@require_role(["MANAGER", "ADMIN"])
def auditoria_create():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json() or {}
    try:
        ar = create_audit_request(
            org_id=user.organizationId,
            actor_id=user_id,
            attempt_id=data.get("attemptId", ""),
            enrollment_id=data.get("enrollmentId", ""),
            reason=data.get("reason", ""),
        )
    except AuditRequestError as exc:
        return jsonify({"message": str(exc)}), 422
    return jsonify(ar), 201
