"""
Servicio de datos para el portal Manager: ranking, matriz, detalle de alumno/intento.
"""
from app.extensions import db
from app.models.training import (
    Convocatoria, Enrollment, EnrollmentStatus,
    AttemptEvent, AuditRequest, AuditStatus,
)
from app.models.session import Attempt, AttemptStatus
from app.models.auth import User


_SEV_TO_FLOAT = {"LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.8, "CRITICAL": 0.95}
_EVENT_LABELS = {
    "HARSH_BRAKING": "Frenada brusca detectada",
    "SPEEDING": "Exceso de velocidad detectado",
    "DEVIATION": "Desviación de ruta detectada",
    "ACCELERATION_LATERAL": "Aceleración lateral excesiva",
    "HARSH_ACCELERATION": "Aceleración brusca detectada",
}


def _fmt_date(dt):
    return dt.strftime("%d/%m/%Y") if dt else "—"


def _fmt_datetime(dt):
    return dt.strftime("%d/%m/%Y %H:%M") if dt else "—"


def _data_quality_label(dq_json):
    if not dq_json:
        return "HIGH"
    if isinstance(dq_json, dict):
        score = dq_json.get("confidenceScore", 1.0)
        if score >= 0.8:
            return "HIGH"
        return "MEDIUM" if score >= 0.5 else "LOW"
    return str(dq_json)


def _conv_to_dict(conv, org_id):
    count = (
        Enrollment.query
        .filter_by(convocatoriaId=conv.id, organizationId=org_id)
        .filter(Enrollment.status != EnrollmentStatus.INVALIDATED)
        .count()
    )
    pending_audits = (
        AuditRequest.query
        .join(Attempt, AuditRequest.originalAttemptId == Attempt.id)
        .filter(
            AuditRequest.organizationId == org_id,
            AuditRequest.status == AuditStatus.PENDING,
            Attempt.convocatoriaId == conv.id,
        )
        .count()
    )
    return {
        "id": conv.id,
        "nombre": conv.name,
        "descripcion": conv.description or "",
        "status": conv.status.value,
        "plazas": conv.plazas,
        "total_candidatos": count,
        "fecha_cierre": _fmt_date(conv.closedAt),
        "ultima_actualizacion": _fmt_datetime(conv.updatedAt),
        "auditorias_pendientes": pending_audits,
    }


def _enrollments_ordered(conv_id, org_id):
    return (
        Enrollment.query
        .filter_by(convocatoriaId=conv_id, organizationId=org_id)
        .filter(Enrollment.status != EnrollmentStatus.INVALIDATED)
        .order_by(Enrollment.enrolledAt)
        .all()
    )


def _plaza(enrollments, enrollment_id):
    for i, e in enumerate(enrollments):
        if e.id == enrollment_id:
            return str(i + 1).zfill(3)
    return "—"


# ── API pública ────────────────────────────────────────────────────────────────

def get_convocatorias(org_id):
    convs = (
        Convocatoria.query
        .filter_by(organizationId=org_id)
        .order_by(Convocatoria.openedAt.desc())
        .all()
    )
    return [_conv_to_dict(c, org_id) for c in convs]


def get_first_conv_id(org_id):
    conv = (
        Convocatoria.query
        .filter_by(organizationId=org_id)
        .order_by(Convocatoria.openedAt.desc())
        .first()
    )
    return conv.id if conv else None


def get_ranking(conv_id, org_id):
    conv = Convocatoria.query.filter_by(id=conv_id, organizationId=org_id).first()
    if not conv:
        return None, []

    enrollments = _enrollments_ordered(conv_id, org_id)
    entries = []

    for idx, enrollment in enumerate(enrollments):
        student = User.query.get(enrollment.studentId)
        if not student:
            continue

        scored = (
            Attempt.query
            .filter_by(enrollmentId=enrollment.id, status=AttemptStatus.CLOSED)
            .filter(Attempt.score.isnot(None))
            .all()
        )
        total = Attempt.query.filter_by(enrollmentId=enrollment.id).count()
        scores = [a.score for a in scored]
        nota_media = sum(scores) / len(scores) if scores else 0.0

        audit_req = AuditRequest.query.filter(
            AuditRequest.organizationId == org_id,
            AuditRequest.requestedBy == enrollment.studentId,
            AuditRequest.status.in_([AuditStatus.PENDING, AuditStatus.REVIEWING]),
        ).first()

        audit_data = None
        if audit_req:
            att = audit_req.original_attempt
            audit_data = {
                "id": audit_req.id,
                "reason": audit_req.reason,
                "fecha": audit_req.createdAt.strftime("%d/%m/%Y") if audit_req.createdAt else "—",
                "hora": audit_req.createdAt.strftime("%H:%M") if audit_req.createdAt else "—",
                "attempt_id": audit_req.originalAttemptId,
                "ruta": att.routeId if att else "—",
            }

        entries.append({
            "nota_media": nota_media,
            "rutas_completadas": len(scored),
            "rutas_total": total,
            "tiene_auditoria": audit_req is not None,
            "audit_data": audit_data,
            "candidato": {
                "id": student.id,
                "nombre": student.name,
                "plaza": str(idx + 1).zfill(3),
                "categoria": "C",
            },
        })

    entries.sort(key=lambda x: x["nota_media"], reverse=True)
    for i, entry in enumerate(entries):
        entry["puesto"] = i + 1
        entry["dentro_del_corte"] = (i + 1) <= conv.plazas

    return _conv_to_dict(conv, org_id), entries


def get_matrix_data(conv_id, org_id):
    conv = Convocatoria.query.filter_by(id=conv_id, organizationId=org_id).first()
    if not conv:
        return None, [], []

    enrollments = _enrollments_ordered(conv_id, org_id)

    scored_attempts = (
        Attempt.query
        .filter_by(convocatoriaId=conv_id, status=AttemptStatus.CLOSED)
        .filter(Attempt.score.isnot(None), Attempt.routeId.isnot(None))
        .all()
    )
    route_ids = sorted({a.routeId for a in scored_attempts})
    circuitos = [{"id": r, "label": r} for r in route_ids]

    candidatos = []
    for idx, enrollment in enumerate(enrollments):
        student = User.query.get(enrollment.studentId)
        if not student:
            continue

        # mejor scored attempt por ruta (mayor score)
        best_by_route: dict = {}
        for a in (
            Attempt.query
            .filter_by(enrollmentId=enrollment.id, status=AttemptStatus.CLOSED)
            .filter(Attempt.score.isnot(None))
            .all()
        ):
            if a.routeId:
                prev = best_by_route.get(a.routeId)
                if prev is None or (a.score or 0) > (prev.score or 0):
                    best_by_route[a.routeId] = a

        notas = {}
        for route_id in route_ids:
            att = best_by_route.get(route_id)
            if att is None:
                notas[route_id] = None
            else:
                has_audit = AuditRequest.query.filter(
                    AuditRequest.originalAttemptId == att.id,
                    AuditRequest.status.in_([AuditStatus.PENDING, AuditStatus.REVIEWING]),
                ).first() is not None
                notas[route_id] = {
                    "nota": att.score,
                    "data_quality": _data_quality_label(att.dataQuality),
                    "audit": has_audit,
                    "attempt_id": att.id,
                }

        total = Attempt.query.filter_by(enrollmentId=enrollment.id).count()
        candidatos.append({
            "id": student.id,
            "nombre": student.name,
            "plaza": str(idx + 1).zfill(3),
            "categoria": "C",
            "notas": notas,
            "rutas_completadas": len(best_by_route),
            "rutas_total": total,
        })

    return _conv_to_dict(conv, org_id), candidatos, circuitos


def get_all_matrix_data(org_id):
    # Obtener todos los alumnos que tienen al menos un enrollment activo
    enrollments = (
        Enrollment.query
        .filter_by(organizationId=org_id)
        .filter(Enrollment.status != EnrollmentStatus.INVALIDATED)
        .all()
    )
    student_ids = {e.studentId for e in enrollments}

    # Obtener todos los intentos cerrados de estos alumnos
    attempts = (
        Attempt.query
        .filter(Attempt.studentId.in_(student_ids))
        .filter_by(organizationId=org_id, status=AttemptStatus.CLOSED)
        .filter(Attempt.score.isnot(None), Attempt.routeId.isnot(None))
        .all()
    )

    route_ids = sorted({a.routeId for a in attempts})
    circuitos = [{"id": r, "label": r} for r in route_ids]

    students = User.query.filter(User.id.in_(student_ids)).all()
    student_map = {s.id: s for s in students}

    candidatos = []
    for sid in student_ids:
        student = student_map.get(sid)
        if not student:
            continue

        # Mejor intento por ruta en TODAS sus participaciones
        best_by_route = {}
        student_attempts = [a for a in attempts if a.studentId == sid]
        for a in student_attempts:
            if a.routeId:
                prev = best_by_route.get(a.routeId)
                if prev is None or (a.score or 0) > (prev.score or 0):
                    best_by_route[a.routeId] = a

        notas = {}
        for route_id in route_ids:
            att = best_by_route.get(route_id)
            if att is None:
                notas[route_id] = None
            else:
                has_audit = AuditRequest.query.filter(
                    AuditRequest.originalAttemptId == att.id,
                    AuditRequest.status.in_([AuditStatus.PENDING, AuditStatus.REVIEWING]),
                ).first() is not None
                notas[route_id] = {
                    "nota": att.score,
                    "data_quality": _data_quality_label(att.dataQuality),
                    "audit": has_audit,
                    "attempt_id": att.id,
                }

        candidatos.append({
            "id": student.id,
            "nombre": student.name,
            "plaza": "—",
            "categoria": "G", # Global
            "notas": notas,
            "rutas_completadas": len(best_by_route),
            "rutas_total": len(student_attempts),
        })

    all_conv_dict = {
        "id": "all",
        "nombre": "Todos los candidatos",
        "descripcion": "Vista global de todos los procesos",
        "status": "OPEN",
        "plazas": 0,
        "total_candidatos": len(candidatos),
        "fecha_cierre": "—",
        "ultima_actualizacion": "—",
        "auditorias_pendientes": 0,
    }

    return all_conv_dict, candidatos, circuitos


def get_alumno_active_conv_id(student_id, org_id):
    enrollment = (
        Enrollment.query
        .join(Convocatoria, Enrollment.convocatoriaId == Convocatoria.id)
        .filter(
            Enrollment.studentId == student_id,
            Enrollment.organizationId == org_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        .order_by(Enrollment.enrolledAt.desc())
        .first()
    )
    return enrollment.convocatoriaId if enrollment else None


def get_alumno_detail(student_id, conv_id, org_id):
    student = User.query.get(student_id)
    if not student:
        return None, None, [], 0.0

    enrollment = Enrollment.query.filter_by(
        studentId=student_id,
        convocatoriaId=conv_id,
        organizationId=org_id,
    ).first()
    if not enrollment:
        return None, None, [], 0.0

    conv = Convocatoria.query.get(conv_id)
    enrollments = _enrollments_ordered(conv_id, org_id)

    scored_attempts = (
        Attempt.query
        .filter_by(enrollmentId=enrollment.id, status=AttemptStatus.CLOSED)
        .filter(Attempt.score.isnot(None))
        .order_by(Attempt.endTime)
        .all()
    )
    total_count = Attempt.query.filter_by(enrollmentId=enrollment.id).count()

    intentos = [
        {
            "ruta_id": a.routeId or "—",
            "ruta_label": a.routeId or "—",
            "nota": a.score,
            "data_quality": _data_quality_label(a.dataQuality),
            "audit": False,  # TODO Tarea 12
            "attempt_id": a.id,
            "fecha": a.endTime.strftime("%d/%m/%Y") if a.endTime else "—",
        }
        for a in scored_attempts
    ]

    scores = [i["nota"] for i in intentos]
    nota_media = sum(scores) / len(scores) if scores else 0.0

    candidato = {
        "id": student.id,
        "nombre": student.name,
        "plaza": _plaza(enrollments, enrollment.id),
        "categoria": "C",
        "rutas_completadas": len(scored_attempts),
        "rutas_total": total_count,
    }

    return _conv_to_dict(conv, org_id) if conv else None, candidato, intentos, nota_media


def _get_auditoria_for_attempt(attempt_id, org_id):
    ar = (
        AuditRequest.query
        .filter_by(originalAttemptId=attempt_id, organizationId=org_id)
        .order_by(AuditRequest.createdAt.desc())
        .first()
    )
    if not ar:
        return None
    return {
        "id": ar.id,
        "status": ar.status.value,
        "reason": ar.reason,
        "resolution": ar.resolution,
        "createdAt": ar.createdAt.strftime("%d/%m/%Y %H:%M") if ar.createdAt else "—",
    }


def get_intento_detail(attempt_id, org_id):
    attempt = Attempt.query.filter_by(id=attempt_id, organizationId=org_id).first()
    if not attempt:
        return None

    student = User.query.get(attempt.studentId) if attempt.studentId else None
    conv = Convocatoria.query.get(attempt.convocatoriaId) if attempt.convocatoriaId else None

    nota_info = {
        "nota": attempt.score or 0.0,
        "data_quality": _data_quality_label(attempt.dataQuality),
        "attempt_id": attempt.id,
    }
    ruta = {"id": attempt.routeId or "—", "label": attempt.routeId or "—"}

    return {
        "attempt_id": attempt.id,
        "candidato": {
            "nombre": student.name if student else "—",
            "id": student.id if student else None,
            "plaza": "—",
            "categoria": "C",
        },
        "ruta": ruta,
        "nota_info": nota_info,
        "score_breakdown": _build_breakdown(attempt, conv),
        "eventos": _build_eventos(attempt.id),
        "auditoria": _get_auditoria_for_attempt(attempt.id, org_id),
        "convocatoria": _conv_to_dict(conv, org_id) if conv else None,
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
        conv.pesosPorFamilia if conv and conv.pesosPorFamilia
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
        conf_float = ev.confidence or 0.5
        desc = (
            ev.payload.get("descripcion")
            if isinstance(ev.payload, dict) and ev.payload.get("descripcion")
            else _EVENT_LABELS.get(ev.type.value, ev.type.value.replace("_", " ").title())
        )
        result.append({
            "tipo": ev.type.value,
            "timestamp": ev.timestamp.strftime("%H:%M:%S") if ev.timestamp else "—",
            "severidad": _SEV_TO_FLOAT.get(sev_name, 0.5),
            "source": ev.source.value if ev.source else "SENSOR",
            "confidence": "HIGH" if conf_float >= 0.7 else "LOW",
            "descripcion": desc,
        })
    return result
