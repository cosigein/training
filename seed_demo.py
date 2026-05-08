"""seed_demo.py — Datos demo realistas para el sistema completo.

Idempotente: ejecutar varias veces no duplica filas. Asume que `setup_db.py` ya
corrió antes (org CMadrid, super/admin/manager seed users existen).

Crea (en orden):
- 1 Vehicle (camión bomberos, identifier=DEMO-V001)
- 11 Students (8 para 2026-A, 3 para 2026-B)
- 11 RfidCards (una por alumno, UID estilo Mifare 4-bytes)
- 2 Convocatorias OPEN (2026-A con 8 rutas y 5 plazas, 2026-B con 4 rutas y 3 plazas)
- 11 Enrollments
- ~30-35 Attempts CLOSED actuales con score 3.0-9.6 y dataQuality HIGH/MEDIUM/LOW
- 5 Attempts "anteriores" para 5 alumnos (alimenta evolución/historial con tendencias)
- AttemptEvents correlacionados con la nota de cada attempt (frenadas, exceso vel., etc.)
- 2 Ranking snapshots PROVISIONAL para 2026-A (hoy + hace 3 días)
- TrainingAuditLog entries por cada acción (convocatoria, enrollment, attempt, score, ranking)

Usage:
    python seed_demo.py
"""
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db
from app.models.auth import User, Organization, UserRole
from app.models.vehicle import Vehicle, VehicleType, VehicleStatus
from app.models.session import Attempt, AttemptStatus
from app.models.training import (
    Convocatoria,
    ConvocatoriaStatus,
    Enrollment,
    EnrollmentStatus,
    AttemptEvent,
    AttemptEventType,
    EventSeverity,
    EventSource,
    Ranking,
    RankingStatus,
    TrainingAuditLog,
    AuditAction,
    RfidCard,
)
from setup_db import get_or_create_user


# ─── Catálogo de rutas (mismas IDs que el mock previo del manager) ──────────

ROUTES_A = [
    ("R01", "Salida Cochera"),
    ("R02", "Maniobra T"),
    ("R03", "Paso Angosto"),
    ("R04", "Marcha Atrás"),
    ("R05", "Curva Pronunciada"),
    ("R06", "Emergencia Urbana"),
    ("R07", "Conducción Nocturna"),
    ("R08", "Terreno Irregular"),
]

ROUTES_B = [
    ("R01", "Salida Cochera"),
    ("R02", "Maniobra T"),
    ("R03", "Paso Angosto"),
    ("R04", "Marcha Atrás"),
]


# ─── Dataset principal: estado actual de cada alumno por ruta ──────────────
# (nombre, email, plaza, categoria, scores_por_ruta).
# scores_por_ruta = {route_id: (nota, dataQuality) | None}.

STUDENTS_A = [
    ("Carlos Rodríguez",  "carlos.rodriguez@cmadrid.com",  "001", "C+E", {
        "R01": (8.8, "HIGH"), "R02": (7.5, "HIGH"), "R03": (5.2, "LOW"),
        "R04": (8.1, "HIGH"), "R05": (7.8, "HIGH"),
        "R06": None, "R07": None, "R08": None,
    }),
    ("María González",    "maria.gonzalez@cmadrid.com",    "002", "C", {
        "R01": (9.2, "HIGH"), "R02": (8.7, "HIGH"), "R03": (8.9, "HIGH"),
        "R04": (9.0, "HIGH"), "R05": (8.5, "HIGH"), "R06": (9.1, "HIGH"),
        "R07": None, "R08": None,
    }),
    ("Javier Martínez",   "javier.martinez@cmadrid.com",   "003", "C+E", {
        "R01": (7.3, "HIGH"), "R02": (4.8, "MEDIUM"), "R03": (3.9, "LOW"),
        "R04": (7.1, "HIGH"),
        "R05": None, "R06": None, "R07": None, "R08": None,
    }),
    ("Ana López",         "ana.lopez@cmadrid.com",         "004", "C", {
        "R01": None, "R02": None, "R03": None, "R04": None,
        "R05": None, "R06": None, "R07": None, "R08": None,
    }),
    ("Pedro Sánchez",     "pedro.sanchez@cmadrid.com",     "005", "C+E", {
        "R01": (9.4, "HIGH"), "R02": (9.0, "HIGH"), "R03": (8.7, "HIGH"),
        "R04": (9.2, "HIGH"), "R05": (8.9, "HIGH"), "R06": (9.1, "HIGH"),
        "R07": (8.8, "HIGH"),
        "R08": None,
    }),
    ("Laura Fernández",   "laura.fernandez@cmadrid.com",   "006", "C", {
        "R01": (7.8, "HIGH"), "R02": (8.2, "HIGH"), "R03": (7.5, "HIGH"),
        "R04": (4.1, "LOW"),  "R05": (7.9, "HIGH"),
        "R06": None, "R07": None, "R08": None,
    }),
    ("Miguel Torres",     "miguel.torres@cmadrid.com",     "007", "C+E", {
        "R01": (7.1, "HIGH"), "R02": (6.8, "HIGH"), "R03": (3.5, "LOW"),
        "R04": (3.2, "LOW"),  "R05": (3.0, "MEDIUM"),
        "R06": None, "R07": None, "R08": None,
    }),
    ("Elena Ruiz",        "elena.ruiz@cmadrid.com",        "008", "C", {
        "R01": (9.6, "HIGH"), "R02": (9.3, "HIGH"), "R03": (9.1, "HIGH"),
        "R04": (9.5, "HIGH"), "R05": (9.4, "HIGH"), "R06": (9.2, "HIGH"),
        "R07": (9.0, "HIGH"), "R08": (9.3, "HIGH"),
    }),
    # Usuarios de prueba rápida creados por setup_db.py — se inscriben aquí
    ("Alumno Uno",        "alumno1@cmadrid.com",           "009", "C", {
        "R01": (7.2, "HIGH"), "R02": (6.5, "HIGH"), "R03": (5.8, "MEDIUM"),
        "R04": (8.0, "HIGH"),
        "R05": None, "R06": None, "R07": None, "R08": None,
    }),
    ("Alumno Dos",        "alumno2@cmadrid.com",           "010", "C+E", {
        "R01": (9.0, "HIGH"), "R02": (8.4, "HIGH"),
        "R03": None, "R04": None, "R05": None, "R06": None, "R07": None, "R08": None,
    }),
]

STUDENTS_B = [
    ("Luis Gómez",        "luis.gomez@cmadrid.com",        "101", "C", {
        "R01": (6.8, "HIGH"), "R02": (7.2, "MEDIUM"),
        "R03": (8.0, "HIGH"), "R04": (5.5, "LOW"),
    }),
    ("Sofía Herrera",     "sofia.herrera@cmadrid.com",     "102", "C", {
        "R01": (9.1, "HIGH"), "R02": (8.9, "HIGH"),
        "R03": (9.5, "HIGH"), "R04": (9.2, "HIGH"),
    }),
    ("Diego Navarro",     "diego.navarro@cmadrid.com",     "103", "C", {
        "R01": (4.5, "HIGH"),
        "R02": None, "R03": None, "R04": None,
    }),
]


# ─── Intentos "anteriores" para tendencias en evolución/historial ───────────
# (email_alumno, route_id, score_anterior, dq_anterior, days_ago_extra).
# Representan el SEGUNDO mejor intento del alumno en esa ruta — el detector
# y el manager siempre toman el mejor por ruta.

PREVIOUS_ATTEMPTS = [
    # María mejoró 7.2 → 9.2 en R01 (subiendo)
    ("maria.gonzalez@cmadrid.com",   "R01", 7.2, "HIGH",   30),
    # Carlos mejoró 5.8 → 7.5 en R02 (subiendo)
    ("carlos.rodriguez@cmadrid.com", "R02", 5.8, "MEDIUM", 28),
    # Javier empeoró 6.5 → 4.8 en R02 (bajando — algo raro pasó)
    ("javier.martinez@cmadrid.com",  "R02", 6.5, "HIGH",   28),
    # Pedro mejoró 8.7 → 9.4 en R01 (subiendo)
    ("pedro.sanchez@cmadrid.com",    "R01", 8.7, "HIGH",   25),
    # Laura empeoró 6.2 → 4.1 en R04 (bajando — fallo del sensor según auditoría)
    ("laura.fernandez@cmadrid.com",  "R04", 6.2, "HIGH",   20),
]


# ─── Catálogo de eventos sintéticos según la nota ──────────────────────────
# Lista de (AttemptEventType, EventSeverity, penaltyPoints, descripcion_es).

def _events_for_score(score):
    """Eventos correlacionados con la nota. Más bajo el score, más eventos serios."""
    if score >= 9.0:
        return []
    if score >= 7.5:
        return [
            (AttemptEventType.HARSH_BRAKING, EventSeverity.LOW, 0.3,
             "Frenada brusca leve — anticipación insuficiente"),
        ]
    if score >= 6.0:
        return [
            (AttemptEventType.HARSH_BRAKING, EventSeverity.MEDIUM, 0.6,
             "Frenada brusca en aproximación a curva"),
            (AttemptEventType.SPEEDING, EventSeverity.LOW, 0.4,
             "Exceso leve de velocidad en tramo recto"),
        ]
    if score >= 5.0:
        return [
            (AttemptEventType.HARSH_BRAKING, EventSeverity.MEDIUM, 0.7,
             "Frenada brusca en zona urbana"),
            (AttemptEventType.SPEEDING, EventSeverity.MEDIUM, 0.6,
             "Velocidad por encima del límite (5-10 km/h)"),
            (AttemptEventType.ACCELERATION_LATERAL, EventSeverity.LOW, 0.4,
             "Aceleración lateral elevada en curva"),
        ]
    if score >= 3.5:
        return [
            (AttemptEventType.HARSH_BRAKING, EventSeverity.HIGH, 0.9,
             "Frenada de emergencia detectada"),
            (AttemptEventType.HARSH_ACCELERATION, EventSeverity.MEDIUM, 0.6,
             "Aceleración brusca tras parada"),
            (AttemptEventType.SPEEDING, EventSeverity.HIGH, 0.8,
             "Exceso de velocidad sostenido (>10 km/h sobre el límite)"),
            (AttemptEventType.ACCELERATION_LATERAL, EventSeverity.MEDIUM, 0.5,
             "Aceleración lateral en curva pronunciada"),
            (AttemptEventType.DEVIATION, EventSeverity.MEDIUM, 0.6,
             "Desviación de la trayectoria recomendada"),
        ]
    return [
        (AttemptEventType.HARSH_BRAKING, EventSeverity.CRITICAL, 1.2,
         "Frenada de emergencia con riesgo de bloqueo"),
        (AttemptEventType.HARSH_BRAKING, EventSeverity.HIGH, 0.9,
         "Frenada brusca repetida"),
        (AttemptEventType.HARSH_ACCELERATION, EventSeverity.HIGH, 0.8,
         "Aceleración brusca con vehículo cargado"),
        (AttemptEventType.SPEEDING, EventSeverity.HIGH, 0.9,
         "Exceso de velocidad continuado"),
        (AttemptEventType.ACCELERATION_LATERAL, EventSeverity.HIGH, 0.7,
         "Aceleración lateral peligrosa en curva"),
        (AttemptEventType.DEVIATION, EventSeverity.HIGH, 0.8,
         "Desviación severa fuera del corredor"),
        (AttemptEventType.DEVIATION, EventSeverity.MEDIUM, 0.5,
         "Reentrada brusca a la trayectoria"),
    ]


def _confidence_for_dq(dq_label):
    return {"HIGH": 0.95, "MEDIUM": 0.75, "LOW": 0.55}.get(dq_label, 0.85)


def _rfid_uid_for_plaza(plaza_str):
    """Genera un UID estilo Mifare 4-bytes a partir del nº de plaza."""
    n = int(plaza_str.lstrip("0") or "0")
    return f"04:00:{(n >> 8) & 0xFF:02X}:{n & 0xFF:02X}"


# ─── Helpers idempotentes ────────────────────────────────────────────────────

def get_or_create_vehicle(org_id, name, plate, identifier):
    vehicle = Vehicle.query.filter_by(licensePlate=plate).first()
    if vehicle:
        print(f"ℹ️  Vehículo {plate} ya existe.")
        return vehicle
    vehicle = Vehicle(
        name=name,
        model="Mercedes Atego 1626 AF",
        licensePlate=plate,
        organizationId=org_id,
        identifier=identifier,
        type=VehicleType.FIRE_TRUCK,
        status=VehicleStatus.ACTIVE,
    )
    db.session.add(vehicle)
    db.session.flush()
    print(f"✅ Vehículo {plate} creado.")
    return vehicle


def get_or_create_convocatoria(org_id, name, plazas, route_principal, description):
    conv = Convocatoria.query.filter_by(name=name, organizationId=org_id).first()
    if conv:
        print(f"ℹ️  Convocatoria '{name}' ya existe.")
        return conv
    conv = Convocatoria(
        organizationId=org_id,
        name=name,
        description=description,
        routePrincipal=route_principal,
        plazas=plazas,
        umbralMin=5.0,
        pesosPorFamilia={"estabilidad": 0.40, "velocidad": 0.30, "ruta": 0.15, "conduccion": 0.15},
        criteriaVersion="v1.0",
        normalizerVersion="v1.0",
        detectorVersion="v1.0",
        status=ConvocatoriaStatus.OPEN,
    )
    db.session.add(conv)
    db.session.flush()
    print(f"✅ Convocatoria '{name}' creada (id={conv.id}, plazas={plazas}).")
    return conv


def get_or_create_enrollment(conv_id, student_id, org_id, route_id):
    e = Enrollment.query.filter_by(convocatoriaId=conv_id, studentId=student_id).first()
    if e:
        return e
    e = Enrollment(
        convocatoriaId=conv_id,
        studentId=student_id,
        organizationId=org_id,
        routeId=route_id,
        status=EnrollmentStatus.ACTIVE,
    )
    db.session.add(e)
    db.session.flush()
    return e


def get_or_create_rfid_card(uid, student, org_id):
    """Crea o devuelve una RfidCard activa por uid+org."""
    card = RfidCard.query.filter_by(uid=uid, organizationId=org_id, active=True).first()
    if card:
        return card
    card = RfidCard(
        uid=uid,
        organizationId=org_id,
        assignedTo=student.id,
        assignedAt=datetime.utcnow(),
        active=True,
    )
    db.session.add(card)
    db.session.flush()
    return card


def _build_attempt(*, conv_id, enrollment_id, student_id, vehicle_id, org_id,
                   route_id, score, dq_label, start, end, attempt_number,
                   sequence):
    confidence = _confidence_for_dq(dq_label)
    return Attempt(
        organizationId=org_id,
        vehicleId=vehicle_id,
        enrollmentId=enrollment_id,
        convocatoriaId=conv_id,
        studentId=student_id,
        routeId=route_id,
        attemptNumber=attempt_number,
        startTime=start,
        endTime=end,
        closedAt=end,
        sequence=sequence,
        sessionNumber=sequence,
        status=AttemptStatus.CLOSED,
        source="kiosk",
        scoreRaw=score,
        score=score,
        scoreBreakdown={
            "estabilidad": round(score * 0.40, 2),
            "velocidad":   round(score * 0.30, 2),
            "ruta":        round(score * 0.15, 2),
            "conduccion":  round(score * 0.15, 2),
        },
        scoreExplanation=f"Demo seed — score {score:.1f}/10 con dataQuality {dq_label}.",
        dataQuality={"label": dq_label, "confidenceScore": confidence, "gaps": []},
        criteriaVersionPinned="v1.0",
        normalizerVersionPinned="v1.0",
        detectorVersionPinned="v1.0",
    )


def _seed_events_for_attempt(attempt, dq_label):
    """Crea AttemptEvents para un attempt según su nota. Idempotente: si ya hay
    eventos para este attempt, no crea más."""
    existing = AttemptEvent.query.filter_by(attemptId=attempt.id).count()
    if existing:
        return 0

    events_spec = _events_for_score(attempt.score or 0)
    if not events_spec:
        return 0

    duration = (attempt.endTime - attempt.startTime).total_seconds()
    step = duration / (len(events_spec) + 1) if duration > 0 else 30
    base_confidence = _confidence_for_dq(dq_label)

    for i, (etype, severity, penalty, desc) in enumerate(events_spec, start=1):
        ts = attempt.startTime + timedelta(seconds=int(step * i))
        ev = AttemptEvent(
            attemptId=attempt.id,
            organizationId=attempt.organizationId,
            type=etype,
            severity=severity,
            source=EventSource.DOBACK_ELITE,
            confidence=round(base_confidence * 0.95, 2),
            penaltyPoints=penalty,
            timestamp=ts,
            payload={
                "descripcion": desc,
                "speedKmh": 38 if etype == AttemptEventType.SPEEDING else None,
                "lateralG": 0.45 if etype == AttemptEventType.ACCELERATION_LATERAL else None,
            },
        )
        db.session.add(ev)
    return len(events_spec)


def create_attempt_with_events_if_missing(*, conv_id, enrollment_id, student_id,
                                          vehicle_id, org_id, route_id, score,
                                          dq_label, days_ago, attempt_number=1,
                                          sequence=1):
    """Idempotente por (enrollmentId, routeId, attemptNumber).
    Crea el Attempt + sus AttemptEvents en una sola pasada."""
    existing = Attempt.query.filter_by(
        enrollmentId=enrollment_id,
        routeId=route_id,
        attemptNumber=attempt_number,
    ).first()
    if existing:
        return existing, 0

    start = datetime.utcnow() - timedelta(days=days_ago, hours=2)
    end = start + timedelta(minutes=15)

    attempt = _build_attempt(
        conv_id=conv_id, enrollment_id=enrollment_id, student_id=student_id,
        vehicle_id=vehicle_id, org_id=org_id, route_id=route_id,
        score=score, dq_label=dq_label, start=start, end=end,
        attempt_number=attempt_number, sequence=sequence,
    )
    db.session.add(attempt)
    db.session.flush()

    n_events = _seed_events_for_attempt(attempt, dq_label)
    return attempt, n_events


# ─── Etapas de seed ──────────────────────────────────────────────────────────

def seed_rfid_cards(students_data, org):
    n = 0
    for (name, email, plaza, _categoria, _scores) in students_data:
        student = User.query.filter_by(email=email).first()
        if not student:
            continue
        uid = _rfid_uid_for_plaza(plaza)
        existed = RfidCard.query.filter_by(uid=uid, organizationId=org.id, active=True).first()
        get_or_create_rfid_card(uid, student, org.id)
        if not existed:
            n += 1
    return n


def seed_students_and_attempts(students_data, conv, vehicle, org):
    """Crea Student + Enrollment + Attempt CURRENT por cada (alumno, ruta)."""
    n_attempts = 0
    n_events = 0
    for idx, (name, email, plaza, categoria, scores_dict) in enumerate(students_data):
        student = get_or_create_user(email, name, "alumno123", UserRole.STUDENT, org.id)
        enrollment = get_or_create_enrollment(conv.id, student.id, org.id, conv.routePrincipal)
        days_offset = max(1, (idx + 1) * 2)
        for route_id, score_data in scores_dict.items():
            if score_data is None:
                continue
            score, dq_label = score_data
            _, n_ev = create_attempt_with_events_if_missing(
                conv_id=conv.id, enrollment_id=enrollment.id,
                student_id=student.id, vehicle_id=vehicle.id, org_id=org.id,
                route_id=route_id, score=score, dq_label=dq_label,
                days_ago=days_offset, attempt_number=2, sequence=2,
            )
            n_attempts += 1
            n_events += n_ev
    return n_attempts, n_events


def seed_previous_attempts(org, vehicle):
    """Inserta los attempts 'anteriores' para que evolución muestre tendencia."""
    n_attempts = 0
    n_events = 0
    for email, route_id, score, dq_label, days_ago in PREVIOUS_ATTEMPTS:
        student = User.query.filter_by(email=email).first()
        if not student:
            continue
        enrollment = (
            Enrollment.query
            .filter_by(studentId=student.id, organizationId=org.id)
            .first()
        )
        if not enrollment:
            continue
        _, n_ev = create_attempt_with_events_if_missing(
            conv_id=enrollment.convocatoriaId, enrollment_id=enrollment.id,
            student_id=student.id, vehicle_id=vehicle.id, org_id=org.id,
            route_id=route_id, score=score, dq_label=dq_label,
            days_ago=days_ago, attempt_number=1, sequence=1,
        )
        n_attempts += 1
        n_events += n_ev
    return n_attempts, n_events




def seed_ranking_snapshots(org, conv):
    """Crea snapshots PROVISIONAL para una convocatoria: hoy y hace 3 días."""
    enrollments = (
        Enrollment.query
        .filter_by(convocatoriaId=conv.id, organizationId=org.id)
        .filter(Enrollment.status != EnrollmentStatus.INVALIDATED)
        .all()
    )
    if not enrollments:
        return 0

    now = datetime.utcnow()
    snapshots = [
        ("hoy",          now.replace(hour=6, minute=0, second=0, microsecond=0)),
        ("hace 3 días",  (now - timedelta(days=3)).replace(hour=6, minute=0, second=0, microsecond=0)),
    ]

    total_inserted = 0
    for label, snapshot_at in snapshots:
        existing = (
            Ranking.query
            .filter_by(convocatoriaId=conv.id, snapshotAt=snapshot_at)
            .first()
        )
        if existing:
            continue

        # Calcular promedio del MEJOR attempt por ruta para cada alumno, en la
        # ventana cronológica del snapshot (attempts cuyo closedAt <= snapshot_at).
        rows = []
        for e in enrollments:
            attempts = (
                Attempt.query
                .filter_by(enrollmentId=e.id, status=AttemptStatus.CLOSED)
                .filter(Attempt.score.isnot(None))
                .filter(Attempt.closedAt <= snapshot_at)
                .all()
            )
            if not attempts:
                rows.append((e, None, 0.0))
                continue
            best_by_route = {}
            for a in attempts:
                if not a.routeId:
                    continue
                prev = best_by_route.get(a.routeId)
                if prev is None or (a.score or 0) > (prev.score or 0):
                    best_by_route[a.routeId] = a
            scores = [a.score for a in best_by_route.values()]
            mean = sum(scores) / len(scores) if scores else 0.0
            best_overall = max(best_by_route.values(), key=lambda a: a.score or 0) if best_by_route else None
            rows.append((e, best_overall, mean))

        rows.sort(key=lambda r: r[2], reverse=True)
        for rank, (e, best_attempt, mean) in enumerate(rows, start=1):
            db.session.add(Ranking(
                convocatoriaId=conv.id,
                attemptId=best_attempt.id if best_attempt else None,
                enrollmentId=e.id,
                studentId=e.studentId,
                score=round(mean, 2),
                rank=rank,
                status=RankingStatus.PROVISIONAL,
                snapshotAt=snapshot_at,
            ))
            total_inserted += 1
        print(f"   📸 Snapshot {label} ({snapshot_at:%d/%m %H:%M}) — {len(rows)} filas.")
    return total_inserted


def seed_audit_log_entries(org):
    """Genera TrainingAuditLog entries por cada entidad creada por el seed.
    Idempotente: si ya existe un log con esa (action, resourceType, resourceId), no duplica.
    """
    admin = User.query.filter_by(email="admin@cmadrid.com").first()
    actor_id = admin.id if admin else None
    actor_role = "ADMIN"
    count = 0

    def log_once(action, resource_type, resource_id, delta, when=None):
        nonlocal count
        if not resource_id:
            return
        existing = (
            TrainingAuditLog.query
            .filter_by(action=action, resourceType=resource_type, resourceId=resource_id)
            .first()
        )
        if existing:
            return
        entry = TrainingAuditLog(
            actorId=actor_id,
            actorRole=actor_role,
            action=action,
            resourceType=resource_type,
            resourceId=resource_id,
            delta=delta,
            organizationId=org.id,
            createdAt=when or datetime.utcnow(),
        )
        db.session.add(entry)
        count += 1

    # Convocatorias
    for conv in Convocatoria.query.filter_by(organizationId=org.id).all():
        log_once(
            AuditAction.CONVOCATORIA_CREATED, "Convocatoria", conv.id,
            {"name": conv.name, "plazas": conv.plazas, "umbralMin": conv.umbralMin},
            when=conv.openedAt,
        )

    # Enrollments
    for e in Enrollment.query.filter_by(organizationId=org.id).all():
        log_once(
            AuditAction.ENROLLMENT_CREATED, "Enrollment", e.id,
            {"convocatoriaId": e.convocatoriaId, "studentId": e.studentId, "routeId": e.routeId},
            when=e.enrolledAt,
        )

    # Attempts (uno por attempt: ATTEMPT_CREATED + SCORE_CALCULATED)
    for a in Attempt.query.filter_by(organizationId=org.id).all():
        log_once(
            AuditAction.ATTEMPT_CREATED, "Attempt", a.id,
            {"routeId": a.routeId, "studentId": a.studentId, "convocatoriaId": a.convocatoriaId},
            when=a.startTime,
        )
        if a.score is not None:
            log_once(
                AuditAction.SCORE_CALCULATED, "Attempt", a.id,
                {"score": a.score, "scoreBreakdown": a.scoreBreakdown},
                when=a.closedAt or a.endTime,
            )

    # Ranking snapshots — un log por snapshot (primer Ranking del grupo)
    seen_snapshots = set()
    for r in Ranking.query.join(Convocatoria, Ranking.convocatoriaId == Convocatoria.id).filter(
        Convocatoria.organizationId == org.id
    ).order_by(Ranking.snapshotAt).all():
        key = (r.convocatoriaId, r.snapshotAt)
        if key in seen_snapshots:
            continue
        seen_snapshots.add(key)
        log_once(
            AuditAction.RANKING_PUBLISHED, "Ranking", r.id,
            {"convocatoriaId": r.convocatoriaId, "status": r.status.value},
            when=r.snapshotAt,
        )

    return count


# ─── Orquestador ─────────────────────────────────────────────────────────────

def seed_demo_data():
    app = create_app()
    with app.app_context():
        org = Organization.query.filter_by(name="CMadrid").first()
        if not org:
            print("❌ Org 'CMadrid' no existe. Corré primero `python setup_db.py`.")
            return

        print("🚒 Sembrando vehículo demo...")
        vehicle = get_or_create_vehicle(
            org.id, "Camión Bomberos Demo", "C-26-001", "DEMO-V001",
        )

        print("📋 Sembrando convocatorias...")
        conv_a = get_or_create_convocatoria(
            org.id, "Convocatoria 2026-A", plazas=5, route_principal="R03",
            description="Conductor de camión · Proceso de oposición pública",
        )
        conv_b = get_or_create_convocatoria(
            org.id, "Convocatoria 2026-B", plazas=3, route_principal="R02",
            description="Conductor de camión · Turno de tarde",
        )

        print(f"👨‍🚒 Sembrando alumnos + enrollments + attempts para {conv_a.name}...")
        n_a, ev_a = seed_students_and_attempts(STUDENTS_A, conv_a, vehicle, org)
        print(f"   → {n_a} attempts, {ev_a} eventos detectados.")

        print(f"👩‍🚒 Sembrando alumnos + enrollments + attempts para {conv_b.name}...")
        n_b, ev_b = seed_students_and_attempts(STUDENTS_B, conv_b, vehicle, org)
        print(f"   → {n_b} attempts, {ev_b} eventos detectados.")

        db.session.commit()

        print("🪪  Sembrando tarjetas RFID demo...")
        n_rfid_a = seed_rfid_cards(STUDENTS_A, org)
        n_rfid_b = seed_rfid_cards(STUDENTS_B, org)
        print(f"   → {n_rfid_a + n_rfid_b} tarjetas creadas (o ya existían).")
        db.session.commit()

        print("📈 Sembrando intentos anteriores (tendencias)...")
        n_prev, ev_prev = seed_previous_attempts(org, vehicle)
        print(f"   → {n_prev} attempts anteriores, {ev_prev} eventos.")
        db.session.commit()


        print("📊 Sembrando ranking snapshots PROVISIONAL...")
        n_rank = seed_ranking_snapshots(org, conv_a)
        n_rank += seed_ranking_snapshots(org, conv_b)
        print(f"   → {n_rank} filas de ranking insertadas.")
        db.session.commit()

        print("🧾 Sembrando audit log...")
        n_log = seed_audit_log_entries(org)
        print(f"   → {n_log} entradas de audit log.")
        db.session.commit()

        total_attempts = n_a + n_b + n_prev
        total_events = ev_a + ev_b + ev_prev
        print()
        print("🎉 Seed demo listo:")
        print(f"   · {total_attempts} attempts (con {total_events} eventos)")
        print(f"   · {n_rank} filas de ranking")
        print(f"   · {n_log} entradas de audit log")
        print(f"   · {n_rfid_a + n_rfid_b} tarjetas RFID")


if __name__ == "__main__":
    seed_demo_data()
