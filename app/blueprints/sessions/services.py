from app.models.session import Attempt, GpsMeasurement, CanMeasurement
from app.models.event import EjecucionEvento
from app.extensions import db


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


attempt_service = AttemptService()

# Alias legacy para call sites no migrados todavía
session_service = attempt_service
