"""Student service — datos del portal del alumno (T11).

El alumno solo accede a datos propios. Toda función verifica ownership por
`studentId` antes de devolver info. Sin datos crudos del sensor.
"""
from app.extensions import db
from app.models.training import (
    Convocatoria,
    Enrollment,
    EnrollmentStatus,
    AttemptEvent,
)
from app.models.session import Attempt, AttemptStatus
from app.models.auth import User

_EVENT_LABELS = {
    "HARSH_BRAKING": ("Frenadas bruscas", "Estabilidad"),
    "HARSH_ACCELERATION": ("Aceleraciones bruscas", "Estabilidad"),
    "ACCELERATION_LATERAL": ("Aceleraciones laterales", "Estabilidad"),
    "SPEEDING": ("Excesos de velocidad", "Velocidad"),
    "DEVIATION": ("Desviaciones de trayectoria", "Ruta"),
}


# ── helpers ──────────────────────────────────────────────────────────────────

def _dq_label(dq_json):
    if not dq_json:
        return "HIGH"
    if isinstance(dq_json, dict):
        score = dq_json.get("confidenceScore", 1.0)
        if score >= 0.8:
            return "HIGH"
        return "MEDIUM" if score >= 0.5 else "LOW"
    return str(dq_json)


def _fmt_date(dt):
    return dt.strftime("%d/%m/%Y") if dt else ""


def _fmt_time(dt):
    return dt.strftime("%H:%M") if dt else ""


def _enrollments_ordered(conv_id, org_id):
    return (
        Enrollment.query
        .filter_by(convocatoriaId=conv_id, organizationId=org_id)
        .filter(Enrollment.status != EnrollmentStatus.INVALIDATED)
        .order_by(Enrollment.enrolledAt)
        .all()
    )


def _plaza_for(enrollments, student_id):
    for i, e in enumerate(enrollments):
        if e.studentId == student_id:
            return str(i + 1).zfill(3)
    return "—"


def _active_enrollment(student_id, org_id, conv_id=None):
    q = (
        Enrollment.query
        .join(Convocatoria, Enrollment.convocatoriaId == Convocatoria.id)
        .filter(
            Enrollment.studentId == student_id,
            Enrollment.organizationId == org_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
    )
    if conv_id:
        q = q.filter(Enrollment.convocatoriaId == conv_id)
    return q.order_by(Enrollment.enrolledAt.desc()).first()


def _attempt_owned(attempt_id, student_id, org_id):
    return Attempt.query.filter_by(
        id=attempt_id, studentId=student_id, organizationId=org_id
    ).first()


def _best_attempt_by_route(enrollment_id):
    closed = (
        Attempt.query
        .filter_by(enrollmentId=enrollment_id, status=AttemptStatus.CLOSED)
        .filter(Attempt.score.isnot(None), Attempt.routeId.isnot(None))
        .all()
    )
    best = {}
    for a in closed:
        prev = best.get(a.routeId)
        if prev is None or (a.score or 0) > (prev.score or 0):
            best[a.routeId] = a
    return best


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


def _build_pedagogico(attempt, ruta_label):
    """Genera el bloque pedagógico desde EVENTOS REALES (no desde la nota)."""
    events = AttemptEvent.query.filter_by(attemptId=attempt.id).all()
    nota = attempt.score or 0.0

    grouped = {}
    for ev in events:
        key = ev.type.value if ev.type else "UNKNOWN"
        grouped.setdefault(key, []).append(ev)

    infracciones = []
    for tipo, lista in grouped.items():
        nombre, familia = _EVENT_LABELS.get(tipo, (tipo.replace("_", " ").title(), "—"))
        puntos = round(sum((ev.penaltyPoints or 0) for ev in lista), 2)
        zonas = [ev.timestamp.strftime("%H:%M:%S") for ev in lista if ev.timestamp]
        zona = (
            ", ".join(zonas[:3]) + (f" (+{len(zonas) - 3} más)" if len(zonas) > 3 else "")
            if zonas else "durante el recorrido"
        )
        infracciones.append({
            "tipo": nombre,
            "cantidad": len(lista),
            "zona": f"{ruta_label} — {zona}",
            "familia": familia,
            "puntos": puntos,
        })

    if nota >= 9:
        resumen = "Recorrido excelente. El sensor no detectó incidencias significativas."
        sugerencias = ["Mantené esta técnica en los próximos circuitos."]
    elif nota >= 7:
        resumen = "Buen recorrido. La técnica general es correcta, queda margen de mejora."
        sugerencias = [
            "Anticipe los frenados con al menos 3 segundos de margen.",
            "Mantenga velocidad constante en los tramos rectos.",
        ]
    elif nota >= 5:
        resumen = "Recorrido aprobado. Hay incidencias claras que se pueden trabajar."
        sugerencias = [
            "Revise los puntos donde aparecen frenadas bruscas.",
            "Ajuste la velocidad antes de entrar a curvas, no durante.",
            "Practique la trayectoria en condiciones controladas antes del próximo intento.",
        ]
    else:
        resumen = "Recorrido con incidencias significativas que afectaron varias familias."
        sugerencias = [
            "Trabaje los frenados progresivos — son el factor con más peso.",
            "Anticipe las curvas: reduzca la velocidad antes de entrar.",
            "Siga el GPS sin desviarse — cada desviación suma puntos negativos.",
            "Considere un repaso en vehículo ligero antes del próximo intento.",
        ]

    return {"resumen": resumen, "infracciones": infracciones, "sugerencias": sugerencias}


# ── API pública ──────────────────────────────────────────────────────────────

def get_student_dashboard(student_id, org_id, conv_id=None):
    """Contexto completo del dashboard del alumno. None si no hay enrollment activo."""
    enrollment = _active_enrollment(student_id, org_id, conv_id)
    if not enrollment:
        return None
    conv = enrollment.convocatoria
    student = User.query.get(student_id)
    if not student or not conv:
        return None

    enrollments = _enrollments_ordered(conv.id, org_id)
    plaza = _plaza_for(enrollments, student_id)
    total_candidatos = len(enrollments)

    best_by_route = _best_attempt_by_route(enrollment.id)

    all_routes_in_conv = sorted({
        a.routeId for a in (
            Attempt.query
            .filter(
                Attempt.convocatoriaId == conv.id,
                Attempt.status == AttemptStatus.CLOSED,
                Attempt.routeId.isnot(None),
            ).all()
        )
    })
    rutas_alumno = sorted(best_by_route.keys())
    rutas_pendientes = [r for r in all_routes_in_conv if r not in rutas_alumno]

    rutas_data = []
    for rid in rutas_alumno + rutas_pendientes:
        att = best_by_route.get(rid)
        if att is not None:
            rutas_data.append({
                "id": rid,
                "label": rid,
                "info": {
                    "nota": att.score,
                    "data_quality": _dq_label(att.dataQuality),
                    "attempt_id": att.id,
                    "fecha": _fmt_date(att.endTime),
                    "hora": _fmt_time(att.endTime),
                },
            })
        else:
            rutas_data.append({"id": rid, "label": rid, "info": None})

    scores = [a.score for a in best_by_route.values()]
    nota_media = round(sum(scores) / len(scores), 2) if scores else 0.0

    medias = []
    for e in enrollments:
        bbr = _best_attempt_by_route(e.id)
        ss = [a.score for a in bbr.values()]
        medias.append((e.studentId, sum(ss) / len(ss) if ss else 0.0))
    medias.sort(key=lambda x: x[1], reverse=True)
    mi_posicion = next(
        (i + 1 for i, (sid, _) in enumerate(medias) if sid == student_id),
        None,
    )
    dentro_del_corte = mi_posicion is not None and mi_posicion <= conv.plazas

    rutas_total = max(len(rutas_alumno) + len(rutas_pendientes), 1)

    total_sesiones = Attempt.query.filter_by(enrollmentId=enrollment.id).count()
    last_attempt = (
        Attempt.query
        .filter_by(enrollmentId=enrollment.id)
        .order_by(Attempt.endTime.desc().nullslast())
        .first()
    )
    ultima = _fmt_date(last_attempt.endTime) if last_attempt and last_attempt.endTime else "—"

    return {
        "candidato": {
            "id": student.id,
            "nombre": student.name,
            "plaza": plaza,
            "categoria": "C",
            "rutas_completadas": len(best_by_route),
            "rutas_total": rutas_total,
            "sesiones": total_sesiones,
            "ultima": ultima,
        },
        "convocatoria": {
            "id": conv.id,
            "nombre": conv.name,
            "fecha_cierre": _fmt_date(conv.closedAt),
        },
        "rutas": rutas_data,
        "nota_media": nota_media,
        "mi_posicion": mi_posicion,
        "total_candidatos": total_candidatos,
        "plazas": conv.plazas,
        "dentro_del_corte": dentro_del_corte,
    }


def get_student_intento(attempt_id, student_id, org_id):
    """Detalle de un intento del propio alumno. None si no es propio."""
    attempt = _attempt_owned(attempt_id, student_id, org_id)
    if not attempt:
        return None

    student = User.query.get(student_id)
    conv = Convocatoria.query.get(attempt.convocatoriaId) if attempt.convocatoriaId else None
    enrollments = _enrollments_ordered(conv.id, org_id) if conv else []
    plaza = _plaza_for(enrollments, student_id)
    pedagogico = _build_pedagogico(attempt, attempt.routeId or "este circuito")

    return {
        "candidato": {"id": student.id, "nombre": student.name, "plaza": plaza, "categoria": "C"},
        "convocatoria": {"id": conv.id, "nombre": conv.name} if conv else None,
        "ruta": {"id": attempt.routeId or "—", "label": attempt.routeId or "—"},
        "attempt_id": attempt.id,
        "nota_info": {
            "nota": attempt.score or 0.0,
            "data_quality": _dq_label(attempt.dataQuality),
            "fecha": _fmt_date(attempt.endTime),
            "hora": _fmt_time(attempt.endTime),
        },
        "score_breakdown": _build_breakdown(attempt, conv),
        "pedagogico": pedagogico,
    }


def get_student_historial(student_id, org_id, conv_id=None):
    """Lista de TODOS los intentos cerrados del alumno en la convocatoria activa."""
    enrollment = _active_enrollment(student_id, org_id, conv_id)
    if not enrollment:
        return None

    conv = enrollment.convocatoria
    student = User.query.get(student_id)

    closed = (
        Attempt.query
        .filter_by(enrollmentId=enrollment.id, status=AttemptStatus.CLOSED)
        .filter(Attempt.score.isnot(None))
        .order_by(Attempt.endTime.desc())
        .all()
    )

    best_ids_by_route = {
        rid: a.id for rid, a in _best_attempt_by_route(enrollment.id).items()
    }


    intentos = []
    for a in closed:
        es_actual = best_ids_by_route.get(a.routeId) == a.id
        intentos.append({
            "ruta_id": a.routeId or "—",
            "label": a.routeId or "—",
            "nota": a.score,
            "data_quality": _dq_label(a.dataQuality),
            "attempt_id": a.id,
            "fecha": _fmt_date(a.endTime),
            "hora": _fmt_time(a.endTime),
            "es_actual": es_actual,
        })

    enrollments = _enrollments_ordered(conv.id, org_id)
    plaza = _plaza_for(enrollments, student_id)

    return {
        "candidato": {"id": student.id, "nombre": student.name, "plaza": plaza},
        "convocatoria": {"id": conv.id, "nombre": conv.name},
        "intentos": intentos,
    }


def get_student_evolucion(student_id, org_id, conv_id=None):
    """Comparación entre intentos por ruta — tendencia."""
    enrollment = _active_enrollment(student_id, org_id, conv_id)
    if not enrollment:
        return None

    conv = enrollment.convocatoria
    student = User.query.get(student_id)

    closed = (
        Attempt.query
        .filter_by(enrollmentId=enrollment.id, status=AttemptStatus.CLOSED)
        .filter(Attempt.score.isnot(None))
        .order_by(Attempt.endTime)
        .all()
    )

    by_route = {}
    for a in closed:
        if not a.routeId:
            continue
        by_route.setdefault(a.routeId, []).append(a)

    best_scores = []
    for lst in by_route.values():
        best = max(lst, key=lambda x: x.score or 0)
        best_scores.append(best.score or 0)
    nota_media = round(sum(best_scores) / len(best_scores), 2) if best_scores else 0.0

    evolucion = []
    for ruta_id, lst in by_route.items():
        last = lst[-1]
        prev = lst[-2] if len(lst) >= 2 else None
        diff_media = round((last.score or 0) - nota_media, 1)

        if prev:
            diff_prev = (last.score or 0) - (prev.score or 0)
            if diff_prev > 0.3:
                tendencia, icono, color = "subiendo", "ph-trend-up", "verde"
            elif diff_prev < -0.3:
                tendencia, icono, color = "bajando", "ph-trend-down", "rojo"
            else:
                tendencia, icono, color = "estable", "ph-minus", "gris"
            signo = "+" if diff_prev >= 0 else ""
            texto_tendencia = f"{signo}{diff_prev:.1f} vs intento anterior"
        else:
            tendencia, icono, color = "primer", "ph-flag", "azul"
            texto_tendencia = "Primer intento de esta ruta"

        evolucion.append({
            "ruta_id": ruta_id,
            "label": ruta_id,
            "nota": last.score,
            "tendencia": tendencia,
            "icono": icono,
            "color": color,
            "texto_tendencia": texto_tendencia,
            "nota_previa": prev.score if prev else None,
            "diff_media": diff_media,
            "attempt_id": last.id,
        })

    mejor = max(evolucion, key=lambda x: x["nota"]) if evolucion else None
    peor = min(evolucion, key=lambda x: x["nota"]) if evolucion else None

    enrollments = _enrollments_ordered(conv.id, org_id)
    plaza = _plaza_for(enrollments, student_id)

    return {
        "candidato": {"id": student.id, "nombre": student.name, "plaza": plaza},
        "convocatoria": {"id": conv.id, "nombre": conv.name},
        "evolucion": evolucion,
        "nota_media": nota_media,
        "mejor": mejor,
        "peor": peor,
    }




def get_active_enrollments_summary(student_id, org_id):
    """Lista resumida de convocatorias activas del alumno, ordenada por inscripción desc."""
    enrollments = (
        Enrollment.query
        .join(Convocatoria, Enrollment.convocatoriaId == Convocatoria.id)
        .filter(
            Enrollment.studentId == student_id,
            Enrollment.organizationId == org_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
        .order_by(Enrollment.enrolledAt.desc())
        .all()
    )
    return [
        {"conv_id": e.convocatoriaId, "nombre": e.convocatoria.name}
        for e in enrollments
        if e.convocatoria
    ]


