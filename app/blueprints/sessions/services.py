from datetime import datetime
from app.models.session import Attempt, AttemptStatus, GpsMeasurement, CanMeasurement
from app.models.event import EjecucionEvento
from app.models.training import TrainingAuditLog, AuditAction
from app.extensions import db


class AttemptError(Exception):
    pass


class AttemptService:
    @staticmethod
    def get_org_attempts(org_id, limit=50):
        return Attempt.query.filter_by(organizationId=org_id)\
            .order_by(Attempt.startTime.desc())\
            .limit(limit).all()

    @staticmethod
    def get_attempt_details(attempt_id, org_id):
        return Attempt.query.filter_by(id=attempt_id, organizationId=org_id).first()

    @staticmethod
    def get_attempt_events(attempt_id):
        return EjecucionEvento.query.filter_by(attemptId=attempt_id)\
            .order_by(EjecucionEvento.triggeredAt.asc()).all()

    @staticmethod
    def get_attempt_gps(attempt_id):
        return GpsMeasurement.query.filter_by(attemptId=attempt_id)\
            .order_by(GpsMeasurement.timestamp.asc()).all()

    @staticmethod
    def delete_attempt(attempt_id, org_id):
        # ondelete=CASCADE en los FK de measurements/events se encarga de los hijos
        deleted = Attempt.query.filter_by(id=attempt_id, organizationId=org_id)\
            .delete(synchronize_session=False)
        db.session.commit()
        return deleted > 0

    @staticmethod
    def close_attempt(attempt_id, org_id, actor_id):
        att = Attempt.query.filter_by(id=attempt_id, organizationId=org_id).first()
        if not att:
            return None
        if att.status != AttemptStatus.OPEN:
            raise AttemptError(
                f"El intento está en estado {att.status.value}, ya fue cerrado o invalidado."
            )
        now = datetime.utcnow()
        att.status = AttemptStatus.CLOSED
        att.closedAt = now
        att.endTime = att.endTime or now
        db.session.add(TrainingAuditLog(
            actorId=actor_id, actorRole="ADMIN",
            action=AuditAction.ATTEMPT_CLOSED,
            resourceType="Attempt", resourceId=att.id,
            delta={"reason": "MANUAL_CLOSE"},
            organizationId=org_id,
        ))
        db.session.commit()
        return att

    @staticmethod
    def invalidate_attempt(attempt_id, org_id, actor_id, reason):
        if not reason or len(reason.strip()) < 10:
            raise AttemptError("La razón de invalidación debe tener al menos 10 caracteres.")
        att = Attempt.query.filter_by(id=attempt_id, organizationId=org_id).first()
        if not att:
            return None
        if att.status == AttemptStatus.INVALIDATED:
            raise AttemptError("El intento ya está invalidado.")
        now = datetime.utcnow()
        att.status = AttemptStatus.INVALIDATED
        att.invalidatedAt = now
        att.invalidatedBy = actor_id
        att.invalidatedReason = reason.strip()
        if not att.closedAt:
            att.closedAt = now
        db.session.add(TrainingAuditLog(
            actorId=actor_id, actorRole="ADMIN",
            action=AuditAction.ATTEMPT_INVALIDATED,
            resourceType="Attempt", resourceId=att.id,
            delta={"reason": reason.strip()},
            organizationId=org_id,
        ))
        db.session.commit()
        return att


attempt_service = AttemptService()

# Alias legacy para call sites no migrados todavía
session_service = attempt_service
