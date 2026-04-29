"""Manager portal — vistas para MANAGER y ADMIN.

Lee de la BD real (queries SQLAlchemy) y materializa la forma de dict que
los templates ya consumen. La estructura del dict (claves `nombre`, `notas`,
`rutas_completadas`, etc.) se mantiene compatible con los `.html` para no
tocar UI.

Stubs pendientes (siguen como `[]` por ahora):
- Auditorías: el modelo `AuditRequest` se entrega en la tarea 12 del roadmap.
  Cuando exista, reemplazar `_load_auditorias_pendientes()` por la query.
- Rutas catalogadas: hoy son constantes locales (`ROUTES_BY_CONV`). Cuando
  exista un modelo `Route` con vínculo a Convocatoria, reemplazar.
"""
from datetime import datetime
from flask import render_template, request, abort, redirect, url_for, flash, jsonify

from app.extensions import db
from app.models.auth import User
from app.models.session import Attempt, AttemptStatus
from app.models.vehicle import Vehicle
from app.models.training import (
    Convocatoria,
    ConvocatoriaStatus,
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
from flask_jwt_extended import get_jwt_identity
from app.utils.decorators import require_role
from . import manager_bp

# ─── Catálogo local de rutas por convocatoria ──────────────────────────────
# TODO: cuando exista el modelo `Route`, mover este catálogo a la tabla.
# Las claves son `Convocatoria.name`. El primer match gana.

ROUTES_BY_CONV = {
    "Convocatoria 2026-A": [
        {"id": "R01", "label": "Salida Cochera"},
        {"id": "R02", "label": "Maniobra T"},
        {"id": "R03", "label": "Paso Angosto"},
        {"id": "R04", "label": "Marcha Atrás"},
        {"id": "R05", "label": "Curva Pronunciada"},
        {"id": "R06", "label": "Emergencia Urbana"},
        {"id": "R07", "label": "Conducción Nocturna"},
        {"id": "R08", "label": "Terreno Irregular"},
    ],
    "Convocatoria 2026-B": [
        {"id": "R01", "label": "Salida Cochera"},
        {"id": "R02", "label": "Maniobra T"},
        {"id": "R03", "label": "Paso Angosto"},
        {"id": "R04", "label": "Marcha Atrás"},
    ],
}

DEFAULT_ROUTES = [
    {"id": "R01", "label": "Ruta 1"},
]


def _routes_for(conv):
    return ROUTES_BY_CONV.get(conv.name, DEFAULT_ROUTES)


# ─── Loaders: BD → dict que el template ya espera ──────────────────────────

def _format_date(dt):
    if not dt:
        return "—"
    return dt.strftime("%d/%m/%Y")


def _format_datetime(dt):
    if not dt:
        return "—"
    return dt.strftime("%d/%m/%Y %H:%M")


def _convocatoria_dict(conv, total_candidatos, auditorias_pendientes):
    routes = _routes_for(conv)
    return {
        "id": conv.id,
        "nombre": conv.name,
        "descripcion": conv.description or "",
        "status": conv.status.value if conv.status else "OPEN",
        "plazas": conv.plazas,
        "total_candidatos": total_candidatos,
        "fecha_cierre": _format_date(conv.closedAt) if conv.closedAt else "Sin cierre",
        "ultima_actualizacion": _format_datetime(conv.updatedAt or conv.openedAt),
        "auditorias_pendientes": auditorias_pendientes,
        "rutas": routes,
    }


def _load_convocatorias_dicts(only_active=True):
    """Lista de convocatorias visibles para el manager."""
    q = Convocatoria.query
    if only_active:
        q = q.filter(Convocatoria.status.in_([
            ConvocatoriaStatus.OPEN,
            ConvocatoriaStatus.PREVIEW,
            ConvocatoriaStatus.CLOSING,
        ]))
    convs = q.order_by(Convocatoria.openedAt.desc()).all()

    result = []
    for c in convs:
        total = db.session.query(Enrollment).filter_by(convocatoriaId=c.id).count()
        # TODO tarea 12: contar AuditRequest pendientes por convocatoria.
        result.append(_convocatoria_dict(c, total_candidatos=total, auditorias_pendientes=0))
    return result


def _load_auditorias_pendientes():
    """Stub — el modelo `AuditRequest` se implementa en tarea 12 del roadmap.

    Cuando exista, reemplazar por:
        AuditRequest.query.filter_by(status='PENDING').all()
    y mapear cada uno al dict {id, attempt_id, candidato, ruta, nota,
    fecha_solicitud, hora_solicitud, razon, status}.
    """
    return []



def _get_org_id():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user.organizationId if user else None


def _resolve_conv_id(org_id):
    conv_id = request.args.get("conv_id")
    if not conv_id:
        conv_id = get_first_conv_id(org_id)
    return conv_id


# ─── RUTAS ──────────────────────────────────────────────────────────────────

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
    # TODO tarea 12: cargar desde AuditRequest. Hoy modelo no existe.
    return "Auditoría no encontrada (modelo AuditRequest pendiente — tarea 12).", 404
