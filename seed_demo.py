"""seed_demo.py — Datos demo para que el dashboard manager se vea con contenido realista.

Idempotente: ejecutar varias veces no duplica filas. Asume que `setup_db.py` ya
corrió antes (org CMadrid, super/admin/manager seed users existen).

Crea (en orden):
- 1 Vehicle (camión bomberos)
- 11 Students (8 para 2026-A, 3 para 2026-B; nombres alineados con el mock previo)
- 2 Convocatorias OPEN (2026-A con 8 rutas y 5 plazas, 2026-B con 4 rutas y 3 plazas)
- 11 Enrollments
- ~30-35 Attempts CLOSED con score 3.0-9.6 y dataQuality HIGH/MEDIUM/LOW

NO crea:
- AuditRequest entries (modelo no existe todavía — pendiente tarea 12 del roadmap)
- Ranking snapshots (lo genera el cron de tarea 9 cuando esté implementado)
- AttemptEvent rows (lo genera el detector de tarea 8)

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
    AuditRequest,
    AuditStatus,
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


# ─── Dataset alineado con el mock previo del dashboard ──────────────────────
# Cada alumno: (nombre, email, plaza, categoria, scores_por_ruta).
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


def create_attempt_if_missing(conv_id, enrollment_id, student_id, vehicle_id,
                              org_id, route_id, score, dq_label, days_ago):
    """Idempotente por (enrollmentId, routeId)."""
    existing = Attempt.query.filter_by(
        enrollmentId=enrollment_id,
        routeId=route_id,
    ).first()
    if existing:
        return existing

    start = datetime.utcnow() - timedelta(days=days_ago, hours=2)
    end = start + timedelta(minutes=15)
    confidence = 0.95 if dq_label == "HIGH" else (0.75 if dq_label == "MEDIUM" else 0.55)

    a = Attempt(
        organizationId=org_id,
        vehicleId=vehicle_id,
        enrollmentId=enrollment_id,
        convocatoriaId=conv_id,
        studentId=student_id,
        routeId=route_id,
        attemptNumber=1,
        startTime=start,
        endTime=end,
        closedAt=end,
        sequence=1,
        sessionNumber=1,
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
    db.session.add(a)
    return a


def seed_students_and_attempts(students_data, conv, vehicle, org):
    counter = 0
    for idx, (name, email, plaza, categoria, scores_dict) in enumerate(students_data):
        student = get_or_create_user(email, name, "alumno123", UserRole.STUDENT, org.id)
        enrollment = get_or_create_enrollment(conv.id, student.id, org.id, conv.routePrincipal)
        days_offset = (idx + 1) * 3  # spread sintético en el tiempo
        for route_id, score_data in scores_dict.items():
            if score_data is None:
                continue
            score, dq_label = score_data
            create_attempt_if_missing(
                conv.id, enrollment.id, student.id, vehicle.id, org.id,
                route_id, score, dq_label, days_ago=days_offset,
            )
            counter += 1
    return counter


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
        n_a = seed_students_and_attempts(STUDENTS_A, conv_a, vehicle, org)
        print(f"   → {n_a} attempts creados (o ya existían).")

        print(f"👩‍🚒 Sembrando alumnos + enrollments + attempts para {conv_b.name}...")
        n_b = seed_students_and_attempts(STUDENTS_B, conv_b, vehicle, org)
        print(f"   → {n_b} attempts creados (o ya existían).")

        db.session.commit()

        print("📝 Sembrando auditorías demo...")
        n_audit = seed_audit_requests(org, conv_a)
        print(f"   → {n_audit} auditorías creadas (o ya existían).")

        db.session.commit()
        total = n_a + n_b
        print(f"🎉 Seed demo listo. Total attempts demo: ~{total}.")


def seed_audit_requests(org, conv):
    """Crea 3 AuditRequests demo para la convocatoria A (idempotente)."""
    # Toma los primeros 3 students con attempts en esta conv
    students_with_attempts = (
        Attempt.query
        .filter_by(convocatoriaId=conv.id, organizationId=org.id)
        .filter(Attempt.score.isnot(None), Attempt.studentId.isnot(None))
        .order_by(Attempt.endTime)
        .limit(3)
        .all()
    )
    if not students_with_attempts:
        return 0

    scenarios = [
        ("El sistema registró una frenada brusca que no ocurrió. Solicito revisión de los datos del sensor durante el tramo final del recorrido.", AuditStatus.PENDING),
        ("El vehículo presentó una falla mecánica en el tramo de curva pronunciada que afectó mi puntuación. Adjunto informe del técnico.", AuditStatus.REVIEWING),
        ("La nota no refleja mi desempeño real. El GPS perdió señal en el tramo interior y eso penalizó mi velocidad incorrectamente.", AuditStatus.PENDING),
    ]

    count = 0
    for attempt, (reason, status) in zip(students_with_attempts, scenarios):
        existing = AuditRequest.query.filter_by(
            originalAttemptId=attempt.id,
            organizationId=org.id,
        ).first()
        if existing:
            continue
        ar = AuditRequest(
            organizationId=org.id,
            originalAttemptId=attempt.id,
            enrollmentId=attempt.enrollmentId,
            requestedBy=attempt.studentId,
            reason=reason,
            status=status,
        )
        db.session.add(ar)
        count += 1
    return count


if __name__ == "__main__":
    seed_demo_data()
