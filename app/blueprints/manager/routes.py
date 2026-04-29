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
from flask import render_template, request, abort

from app.extensions import db
from app.models.auth import User
from app.models.training import (
    Convocatoria,
    ConvocatoriaStatus,
    Enrollment,
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
    )


@manager_bp.route("/auditoria/<audit_id>")
@require_role(["MANAGER", "ADMIN"])
def auditoria_detalle(audit_id):
    # TODO tarea 12: cargar desde AuditRequest. Hoy modelo no existe.
    return "Auditoría no encontrada (modelo AuditRequest pendiente — tarea 12).", 404
