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

from flask import render_template, request
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.auth import User
from app.models.session import Attempt, AttemptStatus
from app.models.training import (
    Convocatoria,
    ConvocatoriaStatus,
    Enrollment,
)
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

def _data_quality_label(attempt):
    """Devuelve 'HIGH' | 'MEDIUM' | 'LOW' a partir del JSONB dataQuality."""
    dq = attempt.dataQuality or {}
    label = dq.get("label")
    if label in ("HIGH", "MEDIUM", "LOW"):
        return label
    score = dq.get("confidenceScore")
    if score is None:
        return "HIGH"  # default optimista cuando no hay data
    if score >= 0.85:
        return "HIGH"
    if score >= 0.65:
        return "MEDIUM"
    return "LOW"


def _format_date(dt):
    if not dt:
        return "—"
    return dt.strftime("%d/%m/%Y")


def _format_datetime(dt):
    if not dt:
        return "—"
    return dt.strftime("%d/%m/%Y %H:%M")


def _candidato_dict(student, convocatoria, idx):
    """Construye el dict de un candidato a partir del User STUDENT y sus attempts.

    `idx` se usa para la "plaza" sintética (001, 002, ...) y mantener el orden estable.
    """
    routes = _routes_for(convocatoria)
    route_ids = [r["id"] for r in routes]

    # Carga sus attempts en esta convocatoria, indexados por routeId (último ganando si hubiera dups).
    attempts = (
        Attempt.query
        .filter_by(convocatoriaId=convocatoria.id, studentId=student.id)
        .order_by(Attempt.attemptNumber.desc())
        .all()
    )
    by_route = {}
    last_dt = None
    for a in attempts:
        if a.routeId in by_route:
            continue  # ya tenemos el más reciente por attemptNumber DESC
        by_route[a.routeId] = a
        if last_dt is None or (a.closedAt and a.closedAt > last_dt):
            last_dt = a.closedAt or a.endTime or a.startTime

    notas = {}
    completadas = 0
    for rid in route_ids:
        a = by_route.get(rid)
        if a is None or a.score is None:
            notas[rid] = None
        else:
            notas[rid] = {
                "nota": float(a.score),
                "data_quality": _data_quality_label(a),
                "audit": False,  # TODO tarea 12: hidratar desde AuditRequest
                "attempt_id": a.id,
            }
            completadas += 1

    plaza_offset = 100 if convocatoria.name.endswith("-B") else 0
    return {
        "id": student.id,
        "convocatoria_id": convocatoria.id,
        "nombre": student.name or student.email,
        "plaza": f"{plaza_offset + idx + 1:03d}",
        "categoria": "C+E" if (idx % 2 == 0) else "C",
        "notas": notas,
        "rutas_completadas": completadas,
        "rutas_total": len(route_ids),
        "sesiones": completadas,
        "ultima": _format_date(last_dt),
    }


def _load_candidatos_for(convocatoria):
    enrollments = (
        Enrollment.query
        .options(joinedload(Enrollment.student))
        .filter_by(convocatoriaId=convocatoria.id)
        .order_by(Enrollment.enrolledAt.asc())
        .all()
    )
    return [
        _candidato_dict(e.student, convocatoria, idx)
        for idx, e in enumerate(enrollments)
        if e.student is not None
    ]


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


# ─── Helpers de presentación (consumen dicts, no BD) ───────────────────────

def _calcular_nota_media(candidato):
    notas = [v["nota"] for v in candidato["notas"].values() if v is not None]
    if not notas:
        return 0.0
    return sum(notas) / len(notas)


def _tiene_auditoria_pendiente(candidato_id, auditorias):
    # Stub: hoy auditorias = []. Cuando tarea 12 esté, comparar por nombre/id.
    return False


def _calcular_ranking(plazas, candidatos):
    entries = []
    for c in candidatos:
        nota_media = _calcular_nota_media(c)
        entries.append({
            "candidato": c,
            "nota_media": nota_media,
            "rutas_completadas": c["rutas_completadas"],
            "rutas_total": c["rutas_total"],
            "tiene_auditoria": False,  # TODO tarea 12
        })
    entries.sort(key=lambda x: x["nota_media"], reverse=True)
    for i, entry in enumerate(entries):
        puesto = i + 1
        entry["puesto"] = puesto
        entry["dentro_del_corte"] = puesto <= plazas
    return entries


def _find_attempt_by_id(attempt_id):
    """Localiza un Attempt + dict de candidato + dict de convocatoria + ruta."""
    attempt = Attempt.query.options(
        joinedload(Attempt.student),
        joinedload(Attempt.convocatoria),
    ).filter_by(id=attempt_id).first()
    if not attempt or not attempt.convocatoria or not attempt.student:
        return None, None, None, None, None

    convs = _load_convocatorias_dicts(only_active=False)
    conv_dict = next((c for c in convs if c["id"] == attempt.convocatoria.id), None)
    if conv_dict is None:
        conv_dict = _convocatoria_dict(attempt.convocatoria, total_candidatos=0, auditorias_pendientes=0)

    candidatos = _load_candidatos_for(attempt.convocatoria)
    candidato_dict = next((c for c in candidatos if c["id"] == attempt.student.id), None)

    ruta = next((r for r in conv_dict["rutas"] if r["id"] == attempt.routeId), None)

    nota_info = None
    if candidato_dict and attempt.routeId in candidato_dict["notas"]:
        nota_info = candidato_dict["notas"][attempt.routeId]

    return attempt, candidato_dict, conv_dict, ruta, nota_info


# ─── RUTAS ──────────────────────────────────────────────────────────────────

@manager_bp.route('/')
@require_role(["MANAGER", "ADMIN"])
def dashboard():
    convocatorias = _load_convocatorias_dicts()
    auditorias = _load_auditorias_pendientes()
    return render_template(
        'manager/dashboard.html',
        active_page='dashboard',
        convocatorias=convocatorias,
        auditorias=auditorias,
        pendientes_total=len(auditorias),
    )


@manager_bp.route('/convocatorias')
@require_role(["MANAGER", "ADMIN"])
def convocatorias():
    return render_template(
        'manager/convocatorias.html',
        active_page='convocatorias',
        convocatorias=_load_convocatorias_dicts(only_active=False),
    )


@manager_bp.route('/matriz')
@require_role(["MANAGER", "ADMIN"])
def matriz():
    convs = _load_convocatorias_dicts()
    if not convs:
        return render_template(
            'manager/matriz.html',
            active_page='matriz',
            candidatos=[],
            circuitos=[],
            convocatoria=None,
            convocatorias=[],
        )

    conv_id = request.args.get('conv_id')
    conv_dict = next((c for c in convs if c["id"] == conv_id), convs[0])
    conv_obj = Convocatoria.query.get(conv_dict["id"])
    candidatos = _load_candidatos_for(conv_obj) if conv_obj else []

    return render_template(
        'manager/matriz.html',
        active_page='matriz',
        candidatos=candidatos,
        circuitos=conv_dict["rutas"],
        convocatoria=conv_dict,
        convocatorias=convs,
    )


@manager_bp.route('/ranking')
@require_role(["MANAGER", "ADMIN"])
def ranking():
    convs = _load_convocatorias_dicts()
    if not convs:
        return render_template(
            'manager/ranking.html',
            active_page='ranking',
            ranking=[],
            plazas=0,
            nota_corte=None,
            convocatoria=None,
            convocatorias=[],
            total_candidatos=0,
        )

    conv_id = request.args.get('conv_id')
    conv_dict = next((c for c in convs if c["id"] == conv_id), convs[0])
    conv_obj = Convocatoria.query.get(conv_dict["id"])
    candidatos = _load_candidatos_for(conv_obj) if conv_obj else []

    plazas = conv_dict["plazas"]
    ranking_entries = _calcular_ranking(plazas, candidatos)
    nota_corte = ranking_entries[plazas - 1]["nota_media"] if len(ranking_entries) >= plazas else None

    return render_template(
        'manager/ranking.html',
        active_page='ranking',
        ranking=ranking_entries,
        plazas=plazas,
        nota_corte=nota_corte,
        convocatoria=conv_dict,
        convocatorias=convs,
        total_candidatos=len(candidatos),
    )


@manager_bp.route('/intento/<attempt_id>')
@require_role(["MANAGER", "ADMIN"])
def intento_detalle(attempt_id):
    attempt, candidato, conv, ruta, nota_info = _find_attempt_by_id(attempt_id)
    if not attempt:
        return "Intento no encontrado", 404

    # Score breakdown desde el JSONB del attempt (con fallback proporcional).
    breakdown_jsonb = attempt.scoreBreakdown or {}
    if breakdown_jsonb:
        score_breakdown = [
            {"familia": "Estabilidad", "obtenido": breakdown_jsonb.get("estabilidad", 0.0), "maximo": 4.0},
            {"familia": "Velocidad",   "obtenido": breakdown_jsonb.get("velocidad", 0.0),   "maximo": 3.0},
            {"familia": "Ruta",        "obtenido": breakdown_jsonb.get("ruta", 0.0),        "maximo": 1.5},
            {"familia": "Conducción",  "obtenido": breakdown_jsonb.get("conduccion", 0.0),  "maximo": 1.5},
        ]
    elif nota_info:
        n = nota_info["nota"]
        score_breakdown = [
            {"familia": "Estabilidad", "obtenido": round(n * 0.40, 1), "maximo": 4.0},
            {"familia": "Velocidad",   "obtenido": round(n * 0.30, 1), "maximo": 3.0},
            {"familia": "Ruta",        "obtenido": round(n * 0.15, 1), "maximo": 1.5},
            {"familia": "Conducción",  "obtenido": round(n * 0.15, 1), "maximo": 1.5},
        ]
    else:
        score_breakdown = []

    # TODO tarea 8: cargar AttemptEvent reales. Por ahora placeholder ilustrativo.
    eventos = []
    if nota_info and nota_info["nota"] < 6:
        eventos.append({
            "tipo": "FRENADA_BRUSCA", "timestamp": "—", "severidad": 0.85,
            "source": "SENSOR", "confidence": "HIGH",
            "descripcion": "Penalización por frenada brusca (placeholder demo).",
        })
    if nota_info and nota_info["data_quality"] == "LOW":
        eventos.append({
            "tipo": "ACELERACION_LATERAL", "timestamp": "—", "severidad": 0.45,
            "source": "SENSOR", "confidence": "LOW",
            "descripcion": "Calidad de datos baja (placeholder demo).",
        })

    return render_template(
        'manager/intento.html',
        active_page='matriz',
        candidato=candidato,
        ruta=ruta,
        nota_info=nota_info,
        attempt_id=attempt_id,
        score_breakdown=score_breakdown,
        eventos=eventos,
        auditoria=None,  # TODO tarea 12
        convocatoria=conv,
    )


@manager_bp.route('/auditoria/<audit_id>')
@require_role(["MANAGER", "ADMIN"])
def auditoria_detalle(audit_id):
    # TODO tarea 12: cargar desde AuditRequest. Hoy modelo no existe.
    return "Auditoría no encontrada (modelo AuditRequest pendiente — tarea 12).", 404


@manager_bp.route('/alumno/<candidato_id>')
@require_role(["MANAGER", "ADMIN"])
def alumno_detalle(candidato_id):
    # candidato_id es el User.id (string uuid)
    student = User.query.get(candidato_id)
    if not student:
        return "Candidato no encontrado", 404

    # Buscamos su enrollment activo más reciente.
    enrollment = (
        Enrollment.query
        .filter_by(studentId=student.id)
        .order_by(Enrollment.enrolledAt.desc())
        .first()
    )
    if not enrollment:
        return "Candidato sin convocatoria asignada", 404

    conv_obj = enrollment.convocatoria
    candidatos = _load_candidatos_for(conv_obj)
    candidato = next((c for c in candidatos if c["id"] == student.id), None)
    if not candidato:
        return "Candidato no encontrado en la convocatoria", 404

    conv_dict = _convocatoria_dict(conv_obj, total_candidatos=len(candidatos), auditorias_pendientes=0)

    intentos = []
    for ruta_id, info in candidato["notas"].items():
        if not info:
            continue
        ruta_label = next((r["label"] for r in conv_dict["rutas"] if r["id"] == ruta_id), ruta_id)
        intentos.append({
            "ruta_id": ruta_id,
            "ruta_label": ruta_label,
            "nota": info["nota"],
            "data_quality": info["data_quality"],
            "audit": info["audit"],
            "attempt_id": info["attempt_id"],
        })

    return render_template(
        'manager/alumno.html',
        active_page='matriz',
        candidato=candidato,
        convocatoria=conv_dict,
        intentos=intentos,
        nota_media=_calcular_nota_media(candidato),
    )
