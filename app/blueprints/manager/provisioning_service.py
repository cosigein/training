"""Provisioning del manager: crear alumnos y abrir attempts en modo offline.

Convocatoria y Enrollment se delegan al `ConvocatoriaService` del blueprint admin,
que ya tiene las validaciones y audit log del dominio.

Errores de negocio levantan `ProvisioningError` para que el caller los traduzca a flash/HTTP.
"""
from datetime import datetime

from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.auth import User, UserRole
from app.models.session import Attempt, AttemptStatus
from app.models.training import (
    Enrollment, EnrollmentStatus,
    Convocatoria, ConvocatoriaStatus,
    Route,
    RfidCard, TrainingAuditLog, AuditAction,
)
from app.models.vehicle import Vehicle


class ProvisioningError(Exception):
    pass


# ── Alumnos ───────────────────────────────────────────────────────────────────

def list_students(org_id):
    return (
        User.query
        .filter_by(organizationId=org_id, role=UserRole.STUDENT)
        .order_by(User.name.asc())
        .all()
    )


def create_student(org_id, actor_id, name, email, password, rfid_uid=None):
    name = (name or "").strip()
    email = (email or "").strip().lower()
    password = (password or "").strip()
    rfid_uid = (rfid_uid or "").strip() or None

    if not name:
        raise ProvisioningError("El nombre es obligatorio.")
    if not email or "@" not in email:
        raise ProvisioningError("Email inválido.")
    if not password or len(password) < 6:
        raise ProvisioningError("La contraseña debe tener al menos 6 caracteres.")

    if User.query.filter_by(email=email).first():
        raise ProvisioningError(f"Ya existe un usuario con email {email}.")

    if rfid_uid:
        existing_card = RfidCard.query.filter_by(uid=rfid_uid, active=True).first()
        if existing_card:
            raise ProvisioningError(f"La tarjeta RFID {rfid_uid} ya está asignada.")

    student = User(
        name=name,
        email=email,
        password=generate_password_hash(password, method="pbkdf2:sha256"),
        role=UserRole.STUDENT,
        organizationId=org_id,
        status="ACTIVE",
    )
    db.session.add(student)
    db.session.flush()  # student.id disponible

    if rfid_uid:
        card = RfidCard(
            uid=rfid_uid,
            organizationId=org_id,
            assignedTo=student.id,
            assignedAt=datetime.utcnow(),
            active=True,
        )
        db.session.add(card)

    db.session.commit()
    return student


# ── Attempts ──────────────────────────────────────────────────────────────────

def open_attempt(org_id, actor_id, enrollment_id, vehicle_id=None, route_id=None):
    """Abre un Attempt en estado OPEN para un Enrollment activo, sin score.

    El TXT del sensor se carga después por la UI de detalle del intento.
    """
    enrollment = Enrollment.query.filter_by(
        id=enrollment_id, organizationId=org_id
    ).first()
    if not enrollment:
        raise ProvisioningError("Inscripción no encontrada.")
    if enrollment.status != EnrollmentStatus.ACTIVE:
        raise ProvisioningError(f"La inscripción no está activa (estado {enrollment.status.value}).")

    conv = Convocatoria.query.filter_by(id=enrollment.convocatoriaId, organizationId=org_id).first()
    if not conv:
        raise ProvisioningError("Convocatoria asociada no encontrada.")
    if conv.status != ConvocatoriaStatus.OPEN:
        raise ProvisioningError("La convocatoria no está OPEN — no se aceptan nuevos intentos.")

    if vehicle_id:
        vehicle = Vehicle.query.filter_by(id=vehicle_id, organizationId=org_id).first()
    else:
        vehicle = Vehicle.query.filter_by(organizationId=org_id).first()
    if not vehicle:
        raise ProvisioningError("No hay vehículos registrados en la organización.")

    final_route = (route_id or "").strip() or enrollment.routeId or conv.routePrincipal

    attempt_count = Attempt.query.filter_by(enrollmentId=enrollment.id).count()
    now = datetime.utcnow()

    attempt = Attempt(
        organizationId=org_id,
        vehicleId=vehicle.id,
        enrollmentId=enrollment.id,
        convocatoriaId=conv.id,
        studentId=enrollment.studentId,
        routeId=final_route,
        source="manager_offline",
        status=AttemptStatus.OPEN,
        startTime=now,
        sequence=attempt_count + 1,
        sessionNumber=attempt_count + 1,
        attemptNumber=attempt_count + 1,
        criteriaVersionPinned=conv.criteriaVersion,
        normalizerVersionPinned=conv.normalizerVersion,
        detectorVersionPinned=conv.detectorVersion,
        uploadedById=actor_id,
    )
    db.session.add(attempt)
    db.session.flush()

    db.session.add(TrainingAuditLog(
        actorId=actor_id,
        actorRole="MANAGER",
        action=AuditAction.ATTEMPT_CREATED,
        resourceType="Attempt",
        resourceId=attempt.id,
        delta={
            "enrollmentId": enrollment.id,
            "routeId": final_route,
            "source": "manager_offline",
            "status": "OPEN",
        },
        organizationId=org_id,
    ))

    db.session.commit()
    return attempt


# ── Datos para forms ──────────────────────────────────────────────────────────

def list_active_enrollments_for_student(org_id, student_id):
    """Devuelve enrollments ACTIVE del alumno con su convocatoria adjunta."""
    return (
        Enrollment.query
        .filter_by(
            studentId=student_id,
            organizationId=org_id,
            status=EnrollmentStatus.ACTIVE,
        )
        .all()
    )


def list_open_convocatorias(org_id):
    return (
        Convocatoria.query
        .filter_by(organizationId=org_id, status=ConvocatoriaStatus.OPEN)
        .order_by(Convocatoria.openedAt.desc())
        .all()
    )


# ── Rutas (catálogo) ──────────────────────────────────────────────────────────

def list_routes(org_id, only_active=False):
    q = Route.query.filter_by(organizationId=org_id)
    if only_active:
        q = q.filter_by(active=True)
    return q.order_by(Route.code.asc()).all()


def get_route_by_code(org_id, code):
    return Route.query.filter_by(organizationId=org_id, code=code).first()


def create_route(org_id, code, name, description=None, distance_km=None, duration_min=None):
    code = (code or "").strip().upper()
    name = (name or "").strip()
    description = (description or "").strip() or None

    if not code:
        raise ProvisioningError("El código de la ruta es obligatorio.")
    if " " in code or len(code) > 32:
        raise ProvisioningError("El código no puede tener espacios y debe ser ≤ 32 caracteres.")
    if not name:
        raise ProvisioningError("El nombre de la ruta es obligatorio.")

    if Route.query.filter_by(organizationId=org_id, code=code).first():
        raise ProvisioningError(f"Ya existe una ruta con código '{code}' en la organización.")

    def _to_float(v, label):
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            raise ProvisioningError(f"{label} debe ser numérico.")

    def _to_int(v, label):
        if v is None or v == "":
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            raise ProvisioningError(f"{label} debe ser entero.")

    route = Route(
        organizationId=org_id,
        code=code,
        name=name,
        description=description,
        distanceKm=_to_float(distance_km, "Distancia (km)"),
        durationMin=_to_int(duration_min, "Duración (min)"),
        active=True,
    )
    db.session.add(route)
    db.session.commit()
    return route


def toggle_route_active(org_id, route_id):
    route = Route.query.filter_by(id=route_id, organizationId=org_id).first()
    if not route:
        raise ProvisioningError("Ruta no encontrada.")
    route.active = not route.active
    db.session.commit()
    return route
