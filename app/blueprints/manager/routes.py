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

# ── DATOS MOCK (modelo Paper Maestro v6) ────────────────────────────────────
# Representan el estado de la Convocatoria 2026-A al día de hoy.
# Nota: las notas son 0-10 por intento; el modelo NO emite apto/no_apto
# por intento — solo al cierre de la convocatoria.

CONVOCATORIAS = [
    {
        "id": "conv-26a",
        "nombre": "Convocatoria 2026-A",
        "descripcion": "Conductor de camión · Proceso de oposición pública",
        "status": "OPEN",
        "plazas": 5,
        "total_candidatos": 8,
        "fecha_cierre": "15/06/2026",
        "ultima_actualizacion": "28/04/2026 06:00",
        "auditorias_pendientes": 2,
        "rutas": [
            {"id": "R01", "label": "Salida Cochera"},
            {"id": "R02", "label": "Maniobra T"},
            {"id": "R03", "label": "Paso Angosto"},
            {"id": "R04", "label": "Marcha Atrás"},
            {"id": "R05", "label": "Curva Pronunciada"},
            {"id": "R06", "label": "Emergencia Urbana"},
            {"id": "R07", "label": "Conducción Nocturna"},
            {"id": "R08", "label": "Terreno Irregular"},
        ],
    },
    {
        "id": "conv-26b",
        "nombre": "Convocatoria 2026-B",
        "descripcion": "Conductor de camión · Turno de tarde",
        "status": "OPEN",
        "plazas": 3,
        "total_candidatos": 12,
        "fecha_cierre": "30/06/2026",
        "ultima_actualizacion": "28/04/2026 06:00",
        "auditorias_pendientes": 0,
        "rutas": [
            {"id": "R01", "label": "Salida Cochera"},
            {"id": "R02", "label": "Maniobra T"},
            {"id": "R03", "label": "Paso Angosto"},
            {"id": "R04", "label": "Marcha Atrás"},
        ],
    },
]

# Candidatos con intentos numéricos (nota 0-10 por ruta).
# None = pendiente (no ha completado esa ruta todavía)
# Cada candidato tiene además flags de auditoría por intento.
CANDIDATOS = [
    {
        "id": 1,
        "convocatoria_id": "conv-26a",
        "nombre": "Carlos Rodríguez",
        "plaza": "001",
        "categoria": "C+E",
        "notas": {
            "R01": {"nota": 8.8, "data_quality": "HIGH", "audit": False, "attempt_id": "att-001"},
            "R02": {"nota": 7.5, "data_quality": "HIGH", "audit": False, "attempt_id": "att-002"},
            "R03": {"nota": 5.2, "data_quality": "LOW",  "audit": True,  "attempt_id": "att-003"},
            "R04": {"nota": 8.1, "data_quality": "HIGH", "audit": False, "attempt_id": "att-004"},
            "R05": {"nota": 7.8, "data_quality": "HIGH", "audit": False, "attempt_id": "att-005"},
            "R06": None, "R07": None, "R08": None,
        },
        "rutas_completadas": 5,
        "rutas_total": 8,
        "sesiones": 5,
        "ultima": "25/04/2026",
    },
    {
        "id": 2,
        "convocatoria_id": "conv-26a",
        "nombre": "María González",
        "plaza": "002",
        "categoria": "C",
        "notas": {
            "R01": {"nota": 9.2, "data_quality": "HIGH", "audit": False, "attempt_id": "att-010"},
            "R02": {"nota": 8.7, "data_quality": "HIGH", "audit": False, "attempt_id": "att-011"},
            "R03": {"nota": 8.9, "data_quality": "HIGH", "audit": False, "attempt_id": "att-012"},
            "R04": {"nota": 9.0, "data_quality": "HIGH", "audit": False, "attempt_id": "att-013"},
            "R05": {"nota": 8.5, "data_quality": "HIGH", "audit": False, "attempt_id": "att-014"},
            "R06": {"nota": 9.1, "data_quality": "HIGH", "audit": False, "attempt_id": "att-015"},
            "R07": None, "R08": None,
        },
        "rutas_completadas": 6,
        "rutas_total": 8,
        "sesiones": 6,
        "ultima": "26/04/2026",
    },
    {
        "id": 3,
        "convocatoria_id": "conv-26a",
        "nombre": "Javier Martínez",
        "plaza": "003",
        "categoria": "C+E",
        "notas": {
            "R01": {"nota": 7.3, "data_quality": "HIGH", "audit": False, "attempt_id": "att-020"},
            "R02": {"nota": 4.8, "data_quality": "MEDIUM","audit": True,  "attempt_id": "att-021"},
            "R03": {"nota": 3.9, "data_quality": "LOW",  "audit": False, "attempt_id": "att-022"},
            "R04": {"nota": 7.1, "data_quality": "HIGH", "audit": False, "attempt_id": "att-023"},
            "R05": None, "R06": None, "R07": None, "R08": None,
        },
        "rutas_completadas": 4,
        "rutas_total": 8,
        "sesiones": 4,
        "ultima": "22/04/2026",
    },
    {
        "id": 4,
        "convocatoria_id": "conv-26a",
        "nombre": "Ana López",
        "plaza": "004",
        "categoria": "C",
        "notas": {
            "R01": None, "R02": None, "R03": None, "R04": None,
            "R05": None, "R06": None, "R07": None, "R08": None,
        },
        "rutas_completadas": 0,
        "rutas_total": 8,
        "sesiones": 0,
        "ultima": "—",
    },
    {
        "id": 5,
        "convocatoria_id": "conv-26a",
        "nombre": "Pedro Sánchez",
        "plaza": "005",
        "categoria": "C+E",
        "notas": {
            "R01": {"nota": 9.4, "data_quality": "HIGH", "audit": False, "attempt_id": "att-030"},
            "R02": {"nota": 9.0, "data_quality": "HIGH", "audit": False, "attempt_id": "att-031"},
            "R03": {"nota": 8.7, "data_quality": "HIGH", "audit": False, "attempt_id": "att-032"},
            "R04": {"nota": 9.2, "data_quality": "HIGH", "audit": False, "attempt_id": "att-033"},
            "R05": {"nota": 8.9, "data_quality": "HIGH", "audit": False, "attempt_id": "att-034"},
            "R06": {"nota": 9.1, "data_quality": "HIGH", "audit": False, "attempt_id": "att-035"},
            "R07": {"nota": 8.8, "data_quality": "HIGH", "audit": False, "attempt_id": "att-036"},
            "R08": None,
        },
        "rutas_completadas": 7,
        "rutas_total": 8,
        "sesiones": 7,
        "ultima": "27/04/2026",
    },
    {
        "id": 6,
        "convocatoria_id": "conv-26a",
        "nombre": "Laura Fernández",
        "plaza": "006",
        "categoria": "C",
        "notas": {
            "R01": {"nota": 7.8, "data_quality": "HIGH", "audit": False, "attempt_id": "att-040"},
            "R02": {"nota": 8.2, "data_quality": "HIGH", "audit": False, "attempt_id": "att-041"},
            "R03": {"nota": 7.5, "data_quality": "HIGH", "audit": False, "attempt_id": "att-042"},
            "R04": {"nota": 4.1, "data_quality": "LOW",  "audit": False, "attempt_id": "att-043"},
            "R05": {"nota": 7.9, "data_quality": "HIGH", "audit": False, "attempt_id": "att-044"},
            "R06": None, "R07": None, "R08": None,
        },
        "rutas_completadas": 5,
        "rutas_total": 8,
        "sesiones": 5,
        "ultima": "24/04/2026",
    },
    {
        "id": 7,
        "convocatoria_id": "conv-26a",
        "nombre": "Miguel Torres",
        "plaza": "007",
        "categoria": "C+E",
        "notas": {
            "R01": {"nota": 7.1, "data_quality": "HIGH", "audit": False, "attempt_id": "att-050"},
            "R02": {"nota": 6.8, "data_quality": "HIGH", "audit": False, "attempt_id": "att-051"},
            "R03": {"nota": 3.5, "data_quality": "LOW",  "audit": False, "attempt_id": "att-052"},
            "R04": {"nota": 3.2, "data_quality": "LOW",  "audit": False, "attempt_id": "att-053"},
            "R05": {"nota": 3.0, "data_quality": "MEDIUM","audit": False,"attempt_id": "att-054"},
            "R06": None, "R07": None, "R08": None,
        },
        "rutas_completadas": 5,
        "rutas_total": 8,
        "sesiones": 5,
        "ultima": "23/04/2026",
    },
    {
        "id": 8,
        "convocatoria_id": "conv-26a",
        "nombre": "Elena Ruiz",
        "plaza": "008",
        "categoria": "C",
        "notas": {
            "R01": {"nota": 9.6, "data_quality": "HIGH", "audit": False, "attempt_id": "att-060"},
            "R02": {"nota": 9.3, "data_quality": "HIGH", "audit": False, "attempt_id": "att-061"},
            "R03": {"nota": 9.1, "data_quality": "HIGH", "audit": False, "attempt_id": "att-062"},
            "R04": {"nota": 9.5, "data_quality": "HIGH", "audit": False, "attempt_id": "att-063"},
            "R05": {"nota": 9.4, "data_quality": "HIGH", "audit": False, "attempt_id": "att-064"},
            "R06": {"nota": 9.2, "data_quality": "HIGH", "audit": False, "attempt_id": "att-065"},
            "R07": {"nota": 9.0, "data_quality": "HIGH", "audit": False, "attempt_id": "att-066"},
            "R08": {"nota": 9.3, "data_quality": "HIGH", "audit": False, "attempt_id": "att-067"},
        },
        "rutas_completadas": 8,
        "rutas_total": 8,
        "sesiones": 8,
        "ultima": "28/04/2026",
    },
    {
        "id": 101,
        "convocatoria_id": "conv-26b",
        "nombre": "Luis Gómez",
        "plaza": "101",
        "categoria": "C",
        "notas": {
            "R01": {"nota": 6.8, "data_quality": "HIGH", "audit": False, "attempt_id": "att-101"},
            "R02": {"nota": 7.2, "data_quality": "MEDIUM", "audit": False, "attempt_id": "att-102"},
            "R03": {"nota": 8.0, "data_quality": "HIGH", "audit": False, "attempt_id": "att-103"},
            "R04": {"nota": 5.5, "data_quality": "LOW", "audit": True, "attempt_id": "att-104"},
        },
        "rutas_completadas": 4,
        "rutas_total": 4,
        "sesiones": 4,
        "ultima": "28/04/2026",
    },
    {
        "id": 102,
        "convocatoria_id": "conv-26b",
        "nombre": "Sofia Herrera",
        "plaza": "102",
        "categoria": "C",
        "notas": {
            "R01": {"nota": 9.1, "data_quality": "HIGH", "audit": False, "attempt_id": "att-111"},
            "R02": {"nota": 8.9, "data_quality": "HIGH", "audit": False, "attempt_id": "att-112"},
            "R03": {"nota": 9.5, "data_quality": "HIGH", "audit": False, "attempt_id": "att-113"},
            "R04": {"nota": 9.2, "data_quality": "HIGH", "audit": False, "attempt_id": "att-114"},
        },
        "rutas_completadas": 4,
        "rutas_total": 4,
        "sesiones": 4,
        "ultima": "28/04/2026",
    },
    {
        "id": 103,
        "convocatoria_id": "conv-26b",
        "nombre": "Diego Navarro",
        "plaza": "103",
        "categoria": "C",
        "notas": {
            "R01": {"nota": 4.5, "data_quality": "HIGH", "audit": False, "attempt_id": "att-121"},
            "R02": None, "R03": None, "R04": None,
        },
        "rutas_completadas": 1,
        "rutas_total": 4,
        "sesiones": 1,
        "ultima": "20/04/2026",
    },
]

# Auditorías pendientes de resolución por el manager
AUDITORIAS = [
    {
        "id": "aud-001",
        "attempt_id": "att-003",
        "candidato": "Carlos Rodríguez",
        "ruta": "Paso Angosto",
        "nota": 5.2,
        "fecha_solicitud": "26/04/2026",
        "hora_solicitud": "17:45",
        "razon": "Hubo un camión en doble fila que me forzó a detenerme bruscamente sin previo aviso. El sistema detectó frenada brusca pero fue causada por un obstáculo ajeno.",
        "status": "PENDING",
    },
    {
        "id": "aud-002",
        "attempt_id": "att-021",
        "candidato": "Javier Martínez",
        "ruta": "Maniobra T",
        "nota": 4.8,
        "fecha_solicitud": "23/04/2026",
        "hora_solicitud": "09:12",
        "razon": "El sensor del camión falló intermitentemente durante la maniobra. La calidad de datos figura como MEDIUM pero creo que hay lecturas erróneas que influyeron en la nota.",
        "status": "PENDING",
    },
]


def _calcular_nota_media(candidato):
    """Calcula la nota media de las rutas completadas."""
    notas = [v["nota"] for v in candidato["notas"].values() if v is not None]
    if not notas:
        return 0.0
    return sum(notas) / len(notas)


def _tiene_auditoria_pendiente(candidato_id):
    nombre = next((c["nombre"] for c in CANDIDATOS if c["id"] == candidato_id), "")
    return any(a["candidato"] == nombre and a["status"] == "PENDING" for a in AUDITORIAS)


def _calcular_ranking(plazas, conv_id):
    """Ordena candidatos por nota media descendente y calcula posición."""
    entries = []
    candidatos_filtrados = [c for c in CANDIDATOS if c.get("convocatoria_id") == conv_id]
    
    for c in candidatos_filtrados:
        nota_media = _calcular_nota_media(c)
        entries.append({
            "candidato": c,
            "nota_media": nota_media,
            "rutas_completadas": c["rutas_completadas"],
            "rutas_total": c["rutas_total"],
            "tiene_auditoria": _tiene_auditoria_pendiente(c["id"]),
        })

    entries.sort(key=lambda x: x["nota_media"], reverse=True)

    for i, entry in enumerate(entries):
        puesto = i + 1
        entry["puesto"] = puesto
        entry["dentro_del_corte"] = puesto <= plazas

    return entries


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
