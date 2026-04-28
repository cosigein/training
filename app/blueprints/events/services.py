from app.models.event import Event, EjecucionEvento
from app.extensions import db

class EventService:
    @staticmethod
    def get_org_events(org_id, limit=100):
        return Event.query.filter_by(organizationId=org_id)\
            .order_by(Event.timestamp.desc())\
            .limit(limit).all()

    @staticmethod
    def get_event(event_id, org_id):
        return Event.query.filter_by(id=event_id, organizationId=org_id).first()

    @staticmethod
    def acknowledge_event(event, user_id):
        event.status = "ACKNOWLEDGED"
        # In a real app, you would record who acknowledged it in an "AccionDisparada" table
        db.session.commit()
        return event

event_service = EventService()
