"""
Servicio de AuditRequest para el portal Manager (T12).
El manager puede listar, ver detalle y resolver auditorías pendientes.
"""
from datetime import datetime

from app.extensions import db
from app.models.training import (
    AuditRequest, AuditStatus,
    TrainingAuditLog, AuditAction,
    Enrollment,
)
from app.models.session import Attempt
from app.models.auth import User


class AuditRequestError(Exception):
    pass


def _to_dict(ar):
    attempt = Attempt.query.get(ar.originalAttemptId) if ar.originalAttemptId else None
    requester = User.query.get(ar.requestedBy) if ar.requestedBy else None
    reviewer = User.query.get(ar.reviewedBy) if ar.reviewedBy else None
    return {
        "id": ar.id,
        "status": ar.status.value,
        "reason": ar.reason,
        "resolution": ar.resolution,
        "filedAfterClose": ar.filedAfterClose,
        "createdAt": ar.createdAt.strftime("%d/%m/%Y %H:%M") if ar.createdAt else "—",
        "reviewedAt": ar.reviewedAt.strftime("%d/%m/%Y %H:%M") if ar.reviewedAt else None,
        "requester": requester.name if requester else "—",
        "reviewer": reviewer.name if reviewer else None,
        "attempt": {
            "id": attempt.id,
            "score": attempt.score,
            "routeId": attempt.routeId or "—",
            "status": attempt.status.value if attempt.status else "—",
        } if attempt else None,
    }


def list_audit_requests(org_id, status=None):
    """Lista de AuditRequest de la organización, opcionalmente filtradas por status."""
    q = AuditRequest.query.filter_by(organizationId=org_id)
    if status:
        try:
            q = q.filter_by(status=AuditStatus(status))
        except ValueError:
            pass
    return [_to_dict(ar) for ar in q.order_by(AuditRequest.createdAt.desc()).all()]


def get_audit_request(audit_id, org_id):
    """Detalle de una AuditRequest."""
    ar = AuditRequest.query.filter_by(id=audit_id, organizationId=org_id).first()
    if not ar:
        return None
    return _to_dict(ar)


def update_audit_request(audit_id, org_id, actor_id, new_status, resolution=None):
    """
    Manager actualiza el estado de una AuditRequest.
    Transiciones válidas: PENDING → REVIEWING → CONFIRMED | REEVALUATED | REJECTED
    """
    ar = AuditRequest.query.filter_by(id=audit_id, organizationId=org_id).first()
    if not ar:
        raise AuditRequestError("Auditoría no encontrada.")

    try:
        status_enum = AuditStatus(new_status)
    except ValueError:
        raise AuditRequestError(f"Estado inválido: {new_status}")

    terminal = {AuditStatus.CONFIRMED, AuditStatus.REEVALUATED, AuditStatus.REJECTED}
    if ar.status in terminal:
        raise AuditRequestError(
            f"La auditoría ya está resuelta ({ar.status.value}) — no se puede modificar."
        )
    if status_enum in terminal and not (resolution or "").strip():
        raise AuditRequestError("Se requiere resolución al cerrar una auditoría.")

    ar.status = status_enum
    ar.reviewedBy = actor_id
    ar.reviewedAt = datetime.utcnow()
    if resolution:
        ar.resolution = resolution.strip()

    db.session.add(TrainingAuditLog(
        actorId=actor_id,
        actorRole="MANAGER",
        action=AuditAction.ATTEMPT_CLOSED,  # reutilizamos acción más cercana disponible
        resourceType="AuditRequest",
        resourceId=audit_id,
        delta={"status": new_status, "resolution": resolution},
        organizationId=org_id,
    ))
    db.session.commit()
    return _to_dict(ar)


def create_audit_request(org_id, actor_id, attempt_id, enrollment_id, reason):
    """Crea una AuditRequest (puede ser disparada por admin o alumno vía API)."""
    if not reason or len(reason.strip()) < 30:
        raise AuditRequestError("La razón debe tener al menos 30 caracteres.")

    attempt = Attempt.query.filter_by(id=attempt_id, organizationId=org_id).first()
    if not attempt:
        raise AuditRequestError("Intento no encontrado.")

    ar = AuditRequest(
        organizationId=org_id,
        originalAttemptId=attempt_id,
        enrollmentId=enrollment_id,
        requestedBy=actor_id,
        reason=reason.strip(),
        status=AuditStatus.PENDING,
    )
    db.session.add(ar)
    db.session.commit()
    return _to_dict(ar)


def count_pending(org_id):
    """Conteo rápido de AuditRequest PENDING para el dashboard."""
    return AuditRequest.query.filter_by(
        organizationId=org_id, status=AuditStatus.PENDING
    ).count()
