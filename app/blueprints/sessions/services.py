from app.models.session import Session, GpsMeasurement, CanMeasurement
from app.models.event import EjecucionEvento
from app.extensions import db

class SessionService:
    @staticmethod
    def get_org_sessions(org_id, limit=50):
        return Session.query.filter_by(organizationId=org_id)\
            .order_by(Session.startTime.desc())\
            .limit(limit).all()

    @staticmethod
    def get_session_details(session_id, org_id):
        session = Session.query.filter_by(id=session_id, organizationId=org_id).first()
        if not session:
            return None
            
        # Optional: Load measurements too
        return session

    @staticmethod
    def get_session_events(session_id):
        return EjecucionEvento.query.filter_by(sessionId=session_id)\
            .order_by(EjecucionEvento.triggeredAt.asc()).all()

    @staticmethod
    def get_session_gps(session_id):
        return GpsMeasurement.query.filter_by(sessionId=session_id)\
            .order_by(GpsMeasurement.timestamp.asc()).all()

session_service = SessionService()
