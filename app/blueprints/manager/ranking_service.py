"""
Servicio de datos para el portal Manager: ranking, matriz, detalle de alumno/intento.
"""
from app.extensions import db
from app.models.training import (
    Convocatoria, Enrollment, EnrollmentStatus,
    AttemptEvent
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
    return {
        "id": conv.id,
        "nombre": conv.name,
        "descripcion": conv.description or "",
        "status": conv.status.value,
        "plazas": conv.plazas,
        "total_candidatos": count,
        "fecha_cierre": _fmt_date(conv.closedAt),
        "ultima_actualizacion": _fmt_datetime(conv.updatedAt),
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

        entries.append({
            "nota_media": nota_media,
            "rutas_completadas": len(scored),
            "rutas_total": total,
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


def _slot_code(seq):
    """Etiqueta visible del intento según su orden cronológico en el enrollment.
    R01, R02, … Si seq es None devuelve None (intento ignorable)."""
    return f"R{seq:02d}" if seq else None


def get_matrix_data(conv_id, org_id):
    conv = Convocatoria.query.filter_by(id=conv_id, organizationId=org_id).first()
    if not conv:
        return None, [], []

    enrollments = _enrollments_ordered(conv_id, org_id)

    scored_attempts = (
        Attempt.query
        .filter_by(convocatoriaId=conv_id, status=AttemptStatus.CLOSED)
        .filter(Attempt.score.isnot(None))
        .all()
    )
    slot_codes = sorted({_slot_code(a.sequence) for a in scored_attempts if a.sequence})
    circuitos = [{"id": s, "label": s} for s in slot_codes]

    candidatos = []
    for idx, enrollment in enumerate(enrollments):
        student = User.query.get(enrollment.studentId)
        if not student:
            continue

        # un Attempt por slot del alumno (cada slot R{N} es único por enrollment)
        attempts_by_slot: dict = {}
        for a in (
            Attempt.query
            .filter_by(enrollmentId=enrollment.id, status=AttemptStatus.CLOSED)
            .filter(Attempt.score.isnot(None))
            .all()
        ):
            slot = _slot_code(a.sequence)
            if slot:
                attempts_by_slot[slot] = a

        notas = {}
        for slot in slot_codes:
            att = attempts_by_slot.get(slot)
            if att is None:
                notas[slot] = None
            else:
                notas[slot] = {
                    "nota": att.score,
                    "data_quality": _data_quality_label(att.dataQuality),
                    "attempt_id": att.id,
                    "route_code": att.routeId or "—",
                }

        total = Attempt.query.filter_by(enrollmentId=enrollment.id).count()
        candidatos.append({
            "id": student.id,
            "nombre": student.name,
            "plaza": str(idx + 1).zfill(3),
            "categoria": "C",
            "notas": notas,
            "rutas_completadas": len(attempts_by_slot),
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
        .filter(Attempt.score.isnot(None))
        .all()
    )

    slot_codes = sorted({_slot_code(a.sequence) for a in attempts if a.sequence})
    circuitos = [{"id": s, "label": s} for s in slot_codes]

    students = User.query.filter(User.id.in_(student_ids)).all()
    student_map = {s.id: s for s in students}

    candidatos = []
    for sid in student_ids:
        student = student_map.get(sid)
        if not student:
            continue

        # un Attempt por slot del alumno (cada slot R{N} es único por enrollment)
        attempts_by_slot = {}
        student_attempts = [a for a in attempts if a.studentId == sid]
        for a in student_attempts:
            slot = _slot_code(a.sequence)
            if slot:
                attempts_by_slot[slot] = a

        notas = {}
        for slot in slot_codes:
            att = attempts_by_slot.get(slot)
            if att is None:
                notas[slot] = None
            else:
                notas[slot] = {
                    "nota": att.score,
                    "data_quality": _data_quality_label(att.dataQuality),
                    "attempt_id": att.id,
                    "route_code": att.routeId or "—",
                }

        candidatos.append({
            "id": student.id,
            "nombre": student.name,
            "plaza": "—",
            "categoria": "G", # Global
            "notas": notas,
            "rutas_completadas": len(attempts_by_slot),
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
        .order_by(Attempt.endTime.desc())
        .all()
    )
    total_count = Attempt.query.filter_by(enrollmentId=enrollment.id).count()

    # 1. Identificar TODAS las rutas de esta convocatoria (basado en intentos de todos los alumnos)
    all_routes_in_conv = db.session.query(Attempt.routeId).filter_by(
        convocatoriaId=conv_id, organizationId=org_id
    ).filter(Attempt.routeId.isnot(None)).distinct().all()
    route_ids = sorted([r[0] for r in all_routes_in_conv])

    # Asegurar que la ruta principal esté presente
    if conv and conv.routePrincipal and conv.routePrincipal not in route_ids:
        route_ids.append(conv.routePrincipal)
        route_ids.sort()

    # 2. Mapear mejor intento del alumno por ruta
    best_attempts = {}
    for a in scored_attempts:
        if a.routeId:
            prev = best_attempts.get(a.routeId)
            if prev is None or (a.score or 0) > (prev.score or 0):
                best_attempts[a.routeId] = a

    intentos = []
    for rid in route_ids:
        a = best_attempts.get(rid)
        if a:
            intentos.append({
                "ruta_id": rid,
                "ruta_label": rid,
                "nota": a.score,
                "data_quality": _data_quality_label(a.dataQuality),
                "attempt_id": a.id,
                "fecha": a.endTime.strftime("%d/%m/%Y") if a.endTime else "—",
                "realizado": True
            })
        else:
            intentos.append({
                "ruta_id": rid,
                "ruta_label": rid,
                "nota": None,
                "realizado": False,
                "fecha": "—"
            })

    # Nota media solo de las realizadas
    scores = [i["nota"] for i in intentos if i["realizado"] and i["nota"] is not None]
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
    slot = _slot_code(attempt.sequence) or "—"
    ruta = {
        "id": slot,
        "label": slot,
        "route_code": attempt.routeId or "—",
    }

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
