"""
Servicio de datos para el portal Student (T11).
El alumno ve sus propias inscripciones, intentos y posición en el ranking.
"""
from app.extensions import db
from app.models.training import (
    Convocatoria, Enrollment, EnrollmentStatus,
    AttemptEvent,
)
from app.models.session import Attempt, AttemptStatus


_SEV_TO_LABEL = {"LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.8, "CRITICAL": 0.95}
_EVENT_LABELS = {
    "HARSH_BRAKING": "Frenada brusca detectada",
    "SPEEDING": "Exceso de velocidad detectado",
    "DEVIATION": "Desviación de ruta detectada",
    "ACCELERATION_LATERAL": "Aceleración lateral excesiva",
    "HARSH_ACCELERATION": "Aceleración brusca detectada",
}


def _dq_label(dq_json):
    if not dq_json:
        return "HIGH"
    if isinstance(dq_json, dict):
        score = dq_json.get("confidenceScore", 1.0)
        if score >= 0.8:
            return "HIGH"
        return "MEDIUM" if score >= 0.5 else "LOW"
    return str(dq_json)


def _compute_position(student_id, conv_id, org_id, nota_media):
    """Posición en el ranking al vuelo (igual que manager/ranking_service)."""
    if nota_media is None:
        return None, 0
    enrollments = (
        Enrollment.query
        .filter_by(convocatoriaId=conv_id, organizationId=org_id)
        .filter(Enrollment.status != EnrollmentStatus.INVALIDATED)
        .all()
    )
    medias = []
    for e in enrollments:
        scored = (
            Attempt.query
            .filter_by(enrollmentId=e.id, status=AttemptStatus.CLOSED)
            .filter(Attempt.score.isnot(None))
            .all()
        )
        scores = [a.score for a in scored]
        medias.append((e.studentId, sum(scores) / len(scores) if scores else 0.0))

    medias.sort(key=lambda x: x[1], reverse=True)
    for i, (sid, _) in enumerate(medias):
        if sid == student_id:
            return i + 1, len(medias)
    return None, len(medias)


def get_student_dashboard(student_id, org_id):
    """Devuelve lista de inscripciones con convocatoria, intentos y ranking."""
    enrollments = (
        Enrollment.query
        .join(Convocatoria, Enrollment.convocatoriaId == Convocatoria.id)
        .filter(
            Enrollment.studentId == student_id,
            Enrollment.organizationId == org_id,
            Enrollment.status != EnrollmentStatus.INVALIDATED,
        )
        .order_by(Enrollment.enrolledAt.desc())
        .all()
    )

    results = []
    for enrollment in enrollments:
        conv = Convocatoria.query.get(enrollment.convocatoriaId)
        if not conv:
            continue

        closed_attempts = (
            Attempt.query
            .filter_by(enrollmentId=enrollment.id, status=AttemptStatus.CLOSED)
            .filter(Attempt.score.isnot(None))
            .order_by(Attempt.endTime)
            .all()
        )
        total_count = Attempt.query.filter_by(enrollmentId=enrollment.id).count()
        scores = [a.score for a in closed_attempts]
        nota_media = round(sum(scores) / len(scores), 2) if scores else None

        puesto, total_candidatos = _compute_position(
            student_id, conv.id, org_id, nota_media
        )

        intentos = [
            {
                "id": a.id,
                "ruta_id": a.routeId or "—",
                "nota": a.score,
                "data_quality": _dq_label(a.dataQuality),
                "fecha": a.endTime.strftime("%d/%m/%Y %H:%M") if a.endTime else "—",
            }
            for a in closed_attempts
        ]

        results.append({
            "conv_id": conv.id,
            "conv_nombre": conv.name,
            "conv_status": conv.status.value,
            "plazas": conv.plazas,
            "umbral_min": conv.umbralMin,
            "nota_media": nota_media,
            "puesto": puesto,
            "total_candidatos": total_candidatos,
            "dentro_del_corte": puesto is not None and puesto <= conv.plazas,
            "rutas_completadas": len(closed_attempts),
            "rutas_total": total_count,
            "intentos": intentos,
        })

    return results


def get_student_intento(attempt_id, student_id, org_id):
    """Detalle de un intento. Solo accesible si pertenece al alumno."""
    attempt = Attempt.query.filter_by(
        id=attempt_id,
        studentId=student_id,
        organizationId=org_id,
    ).first()
    if not attempt:
        return None

    conv = Convocatoria.query.get(attempt.convocatoriaId) if attempt.convocatoriaId else None

    breakdown = _build_breakdown(attempt, conv)
    eventos = _build_eventos(attempt.id)

    return {
        "id": attempt.id,
        "ruta_id": attempt.routeId or "—",
        "nota": attempt.score or 0.0,
        "data_quality": _dq_label(attempt.dataQuality),
        "fecha": attempt.endTime.strftime("%d/%m/%Y %H:%M") if attempt.endTime else "—",
        "conv_nombre": conv.name if conv else "—",
        "conv_id": conv.id if conv else None,
        "score_breakdown": breakdown,
        "eventos": eventos,
    }


def _build_breakdown(attempt, conv):
    if attempt.scoreBreakdown and isinstance(attempt.scoreBreakdown, dict):
        pesos = conv.pesosPorFamilia if conv and conv.pesosPorFamilia else {}
        return [
            {
                "familia": fam.capitalize(),
                "obtenido": round(val, 1),
                "maximo": round(pesos.get(fam, 0.25) * 10, 1),
            }
            for fam, val in attempt.scoreBreakdown.items()
        ]
    score = attempt.score or 0.0
    pesos = (
        conv.pesosPorFamilia
        if conv and conv.pesosPorFamilia
        else {"estabilidad": 0.40, "velocidad": 0.30, "ruta": 0.15, "conduccion": 0.15}
    )
    return [
        {
            "familia": fam.capitalize(),
            "obtenido": round(score * peso, 1),
            "maximo": round(peso * 10, 1),
        }
        for fam, peso in pesos.items()
    ]


def _build_eventos(attempt_id):
    events = (
        AttemptEvent.query
        .filter_by(attemptId=attempt_id)
        .order_by(AttemptEvent.timestamp)
        .all()
    )
    result = []
    for ev in events:
        sev_name = ev.severity.value if ev.severity else "LOW"
        desc = (
            ev.payload.get("descripcion")
            if isinstance(ev.payload, dict) and ev.payload.get("descripcion")
            else _EVENT_LABELS.get(ev.type.value, ev.type.value.replace("_", " ").title())
        )
        result.append({
            "tipo": ev.type.value,
            "timestamp": ev.timestamp.strftime("%H:%M:%S") if ev.timestamp else "—",
            "severidad": _SEV_TO_LABEL.get(sev_name, 0.5),
            "descripcion": desc,
        })
    return result
