"""
Servicio del kiosko: procesar taps RFID.

Flujo del tap (PDF §2):
  1. Validar kiosko (mapeado a Vehicle.identifier)
  2. Validar tarjeta (RfidCard activa, asignada a un STUDENT)
  3. Verificar que el alumno tenga Enrollment ACTIVE en una Convocatoria OPEN
  4. Si hay un Attempt OPEN previo en este kiosko → cerrarlo (NEXT_TAP)
  5. Crear nuevo Attempt con versiones criteria/normalizer/detector PINNED
  6. Audit log
"""
from datetime import datetime
from app.extensions import db
from app.models.auth import User, UserRole, Organization
from app.models.vehicle import Vehicle
from app.models.session import Attempt, AttemptStatus
from app.models.training import (
    RfidCard, Convocatoria, ConvocatoriaStatus,
    Enrollment, EnrollmentStatus,
    TrainingAuditLog, AuditAction,
)


class KioskoError(Exception):
    """Error del flujo de kiosko. `code` mapea a HTTP status."""
    def __init__(self, message, code="kiosk_error", http=400):
        super().__init__(message)
        self.code = code
        self.http = http


def _resolve_org():
    """V1 single-tenant: el kiosko opera contra la primera Organization (CMadrid).
    En V2 esto pasa por kioskCode → Vehicle.organizationId."""
    return Organization.query.first()


def _resolve_active_conv(org_id):
    return (
        Convocatoria.query
        .filter_by(organizationId=org_id, status=ConvocatoriaStatus.OPEN)
        .order_by(Convocatoria.openedAt.desc())
        .first()
    )


def resolve_enrollment_by_plaza(plaza_str, conv_id=None):
    """Mapea un nº de plaza tipeado al Enrollment correspondiente.
    El nº de plaza es el orden de inscripción dentro de la convocatoria activa.
    Devuelve (enrollment, convocatoria, organization) o None si no se resuelve."""
    if not plaza_str:
        return None
    org = _resolve_org()
    if not org:
        return None
    
    if conv_id:
        conv = Convocatoria.query.filter_by(id=conv_id, organizationId=org.id).first()
    else:
        conv = _resolve_active_conv(org.id)
        
    if not conv:
        return None
        
    enrollments = (
        Enrollment.query
        .filter_by(convocatoriaId=conv.id, organizationId=org.id)
        .filter(Enrollment.status != EnrollmentStatus.INVALIDATED)
        .order_by(Enrollment.enrolledAt)
        .all()
    )
    try:
        idx = int(plaza_str.lstrip("0") or "0") - 1
    except ValueError:
        return None
    if idx < 0 or idx >= len(enrollments):
        return None
    return enrollments[idx], conv, org


def get_plaza_for_student(student_id):
    """Devuelve el nº de plaza (como string) para un estudiante dado en una convocatoria abierta.
    Se usa para el redireccionamiento post-login RFID al portal del kiosko."""
    if not student_id:
        return None
    org = _resolve_org()
    if not org:
        return None
    
    # Buscamos una inscripción activa del alumno en la convocatoria OPEN más reciente
    enrollment = (
        Enrollment.query
        .join(Convocatoria, Enrollment.convocatoriaId == Convocatoria.id)
        .filter(
            Enrollment.studentId == student_id,
            Enrollment.organizationId == org.id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
            Convocatoria.status == ConvocatoriaStatus.OPEN
        )
        .order_by(Convocatoria.openedAt.desc())
        .first()
    )

    if not enrollment:
        return None

    conv = enrollment.convocatoria

    # Calcular su posición (plaza) en la lista ordenada de esa convocatoria
    enrollments = (
        Enrollment.query
        .filter_by(convocatoriaId=conv.id, organizationId=org.id)
        .filter(Enrollment.status != EnrollmentStatus.INVALIDATED)
        .order_by(Enrollment.enrolledAt)
        .all()
    )

    for idx, e in enumerate(enrollments):
        if e.id == enrollment.id:
            return str(idx + 1), conv.id

    return None, None



def resolve_attempt_view(attempt_id):
    """Devuelve (attempt, organization) o None si no existe."""
    org = _resolve_org()
    if not org:
        return None
    attempt = Attempt.query.filter_by(id=attempt_id, organizationId=org.id).first()
    return (attempt, org) if attempt else None


class KioskoService:

    @staticmethod
    def process_tap(kiosk_code, rfid_uid):
        if not kiosk_code or not rfid_uid:
            raise KioskoError("Faltan kioskCode y/o rfidUid", code="bad_request", http=400)

        # 1. Validar kiosko (Vehicle.identifier)
        vehicle = Vehicle.query.filter_by(identifier=kiosk_code).first()
        if not vehicle or not vehicle.active:
            raise KioskoError("Kiosko no encontrado o inactivo", code="kiosk_unknown", http=404)

        # 2. Validar tarjeta
        card = RfidCard.query.filter_by(uid=rfid_uid, active=True)\
            .filter(RfidCard.revokedAt.is_(None)).first()
        if not card:
            raise KioskoError("Tarjeta RFID no reconocida", code="card_unknown", http=404)
        if not card.assignedTo:
            raise KioskoError("Tarjeta sin alumno asignado", code="card_unassigned", http=403)

        # 3. Validar usuario
        student = User.query.get(card.assignedTo)
        if not student:
            raise KioskoError("Usuario asignado a la tarjeta no existe", code="student_missing", http=404)
        student_role = student.role.value if hasattr(student.role, "value") else student.role
        if student_role != UserRole.STUDENT.value:
            raise KioskoError(
                f"Usuario tiene rol {student_role}, no STUDENT",
                code="not_student", http=403,
            )
        if student.organizationId != vehicle.organizationId:
            raise KioskoError(
                "Alumno y kiosko de organizaciones distintas",
                code="org_mismatch", http=403,
            )

        # 4. Buscar enrollment activo en convocatoria OPEN
        enrollment = (
            Enrollment.query
            .join(Convocatoria, Enrollment.convocatoriaId == Convocatoria.id)
            .filter(
                Enrollment.studentId == student.id,
                Enrollment.organizationId == vehicle.organizationId,
                Enrollment.status == EnrollmentStatus.ACTIVE,
                Convocatoria.status == ConvocatoriaStatus.OPEN,
            )
            .first()
        )
        if not enrollment:
            raise KioskoError(
                "El alumno no tiene una inscripción activa en una convocatoria abierta",
                code="no_enrollment", http=404,
            )
        convocatoria = enrollment.convocatoria

        org_id = vehicle.organizationId
        now = datetime.utcnow()

        # 5. Cerrar attempt previo OPEN en este kiosko (si existe)
        previous = Attempt.query.filter_by(
            vehicleId=vehicle.id, status=AttemptStatus.OPEN
        ).first()
        if previous:
            previous.status = AttemptStatus.CLOSED
            previous.closedAt = now
            previous.endTime = previous.endTime or now
            db.session.add(TrainingAuditLog(
                actorId=None, actorRole="KIOSK",
                action=AuditAction.ATTEMPT_CLOSED,
                resourceType="Attempt", resourceId=previous.id,
                delta={
                    "reason": "NEXT_TAP",
                    "closedByStudentId": student.id,
                    "closedByRfidUid": rfid_uid,
                },
                organizationId=org_id,
            ))

        # 6. Crear nuevo attempt
        attempt = Attempt(
            organizationId=org_id,
            vehicleId=vehicle.id,
            studentId=student.id,
            enrollmentId=enrollment.id,
            convocatoriaId=convocatoria.id,
            kioskCode=kiosk_code,
            attemptNumber=(enrollment.attemptsCount or 0) + 1,
            startTime=now,
            sequence=1,
            sessionNumber=1,
            source="kiosko",
            status=AttemptStatus.OPEN,
            criteriaVersionPinned=convocatoria.criteriaVersion,
            normalizerVersionPinned=convocatoria.normalizerVersion,
            detectorVersionPinned=convocatoria.detectorVersion,
        )
        db.session.add(attempt)
        db.session.flush()

        db.session.add(TrainingAuditLog(
            actorId=None, actorRole="KIOSK",
            action=AuditAction.ATTEMPT_CREATED,
            resourceType="Attempt", resourceId=attempt.id,
            delta={
                "kioskCode": kiosk_code,
                "rfidUid": rfid_uid,
                "studentId": student.id,
                "enrollmentId": enrollment.id,
                "convocatoriaId": convocatoria.id,
                "criteriaVersionPinned": attempt.criteriaVersionPinned,
            },
            organizationId=org_id,
        ))

        db.session.commit()
        return attempt, previous


kiosko_service = KioskoService()
