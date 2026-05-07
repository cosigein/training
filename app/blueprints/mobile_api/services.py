"""Helpers del blueprint mobile_api.

Implementación incremental por PR. Cada función documenta el PR donde se completa.

Notas clave del modelo:
- `User.managedConvocatorias` es `db.Column(JSONB, default=[])` con la LISTA DE IDs de
  convocatorias supervisadas — NO un relationship. Patrón de query:
  `Convocatoria.query.filter(Convocatoria.id.in_(user.managedConvocatorias or []))`.
- `_conv_to_dict` (manager.ranking_service) devuelve keys en español + fechas formateadas
  dd/mm/yyyy. La API V1 usa camelCase + ISO 8601, así que NO se reusa directo. En su lugar
  construimos el dict camelCase desde el modelo (`_convocatoria_to_camel`).
"""

from app.extensions import db
from app.models.auth import User, UserRole
from app.models.training import Convocatoria, Enrollment, EnrollmentStatus


def _iso(dt):
    """Devuelve datetime → ISO8601 con sufijo Z; None → None."""
    if dt is None:
        return None
    return dt.isoformat() + ("Z" if dt.tzinfo is None else "")


def _convocatoria_to_camel(conv, total_candidates):
    return {
        "id": conv.id,
        "name": conv.name,
        "description": conv.description or "",
        "status": conv.status.value if conv.status else None,
        "plazas": conv.plazas,
        "totalCandidates": total_candidates,
        "closedAt": _iso(conv.closedAt),
        "updatedAt": _iso(conv.updatedAt),
    }


def _count_active_enrollments(conv_id, org_id):
    return (
        Enrollment.query
        .filter_by(convocatoriaId=conv_id, organizationId=org_id)
        .filter(Enrollment.status != EnrollmentStatus.INVALIDATED)
        .count()
    )


def convocatorias_for_user(user):
    """Lista de convocatorias visibles según el rol del user (V1 read-only)."""
    role = user.role.value if hasattr(user.role, "value") else user.role
    org_id = user.organizationId

    if role == UserRole.STUDENT.value:
        rows = (
            db.session.query(Convocatoria)
            .join(Enrollment, Enrollment.convocatoriaId == Convocatoria.id)
            .filter(
                Enrollment.studentId == user.id,
                Enrollment.organizationId == org_id,
                Enrollment.status != EnrollmentStatus.INVALIDATED,
            )
            .order_by(Convocatoria.openedAt.desc())
            .all()
        )
    elif role == UserRole.MANAGER.value:
        managed_ids = user.managedConvocatorias or []
        if not managed_ids:
            return []
        rows = (
            Convocatoria.query
            .filter(
                Convocatoria.id.in_(managed_ids),
                Convocatoria.organizationId == org_id,
            )
            .order_by(Convocatoria.openedAt.desc())
            .all()
        )
    elif role in (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value):
        rows = (
            Convocatoria.query
            .filter_by(organizationId=org_id)
            .order_by(Convocatoria.openedAt.desc())
            .all()
        )
    else:
        # VIEWER, OPERATOR (legacy) — sin acceso en V1
        return []

    return [_convocatoria_to_camel(c, _count_active_enrollments(c.id, org_id)) for c in rows]


def get_convocatoria_detail(conv_id, user):
    """Detalle de una convocatoria scoped a la org del user. None si no existe o no pertenece."""
    conv = (
        Convocatoria.query
        .filter_by(id=conv_id, organizationId=user.organizationId)
        .first()
    )
    if not conv:
        return None
    return _convocatoria_to_camel(conv, _count_active_enrollments(conv_id, user.organizationId))


def can_user_view_attempt(user, attempt):
    """MANAGER/ADMIN/SUPER_ADMIN → siempre. STUDENT → solo si propio."""
    role = user.role.value if hasattr(user.role, "value") else user.role
    if role in (UserRole.MANAGER.value, UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value):
        return True
    if role == UserRole.STUDENT.value:
        return attempt.studentId == user.id
    return False


def remap_ranking_entry(entry_dict):
    """Convierte un entry de manager.ranking_service.get_ranking → camelCase V1.

    NO incluye `withinCutoff` (decisión D-API-001, GDPR art. 22).
    """
    cand = entry_dict.get("candidato") or {}
    return {
        "position": entry_dict.get("puesto"),
        "candidate": {
            "id": cand.get("id"),
            "name": cand.get("nombre"),
            "plaza": cand.get("plaza"),
        },
        "score": entry_dict.get("nota_media"),
        "attemptsCompleted": entry_dict.get("rutas_completadas"),
        "attemptsTotal": entry_dict.get("rutas_total"),
    }


def remap_matrix_row(candidato_dict, circuit_ids):
    """Convierte una row de manager.ranking_service.get_matrix_data → MatrixRow camelCase.

    `notas` del manager es un dict {routeId: {nota, data_quality, attempt_id}}
    que se aplana a una lista [{circuitId, score}] siguiendo el orden de circuit_ids.
    """
    notas = candidato_dict.get("notas") or {}
    scores = []
    for circuit_id in circuit_ids:
        cell = notas.get(circuit_id)
        score_val = cell.get("nota") if isinstance(cell, dict) else None
        scores.append({"circuitId": circuit_id, "score": score_val})
    return {
        "candidate": {
            "id": candidato_dict.get("id"),
            "name": candidato_dict.get("nombre"),
        },
        "scores": scores,
    }


def remap_attempt(attempt_dict):
    """Convierte dict de manager.ranking_service.get_intento_detail → AttemptDetail camelCase V1."""
    cand = attempt_dict.get("candidato") or {}
    nota_info = attempt_dict.get("nota_info") or {}
    ruta = attempt_dict.get("ruta") or {}
    breakdown = attempt_dict.get("score_breakdown") or []
    eventos = attempt_dict.get("eventos") or []
    conv = attempt_dict.get("convocatoria") or {}

    return {
        "id": attempt_dict.get("attempt_id"),
        "candidate": {
            "id": cand.get("id"),
            "name": cand.get("nombre"),
        },
        "route": {
            "id": ruta.get("id"),
            "label": ruta.get("label"),
        },
        "score": nota_info.get("nota"),
        "dataQuality": nota_info.get("data_quality"),
        "scoreBreakdown": [
            {
                "family": item.get("familia"),
                "obtained": item.get("obtenido"),
                "max": item.get("maximo"),
            }
            for item in breakdown
        ],
        "events": [
            {
                "type": ev.get("tipo"),
                "severity": ev.get("severidad"),
                "confidence": ev.get("confidence"),
                "description": ev.get("descripcion"),
                "timestamp": ev.get("timestamp"),
                "source": ev.get("source"),
            }
            for ev in eventos
        ],
        "convocatoriaId": conv.get("id") if conv else None,
    }
