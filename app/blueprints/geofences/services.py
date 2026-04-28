from app.models.geofence import Geofence, Park, Zone
from app.extensions import db

class GeofenceService:
    @staticmethod
    def get_org_geofences(org_id):
        return Geofence.query.filter_by(organizationId=org_id).all()

    @staticmethod
    def get_geofence(geofence_id, org_id):
        return Geofence.query.filter_by(id=geofence_id, organizationId=org_id).first()

    @staticmethod
    def get_org_parks(org_id):
        return Park.query.filter_by(organizationId=org_id).all()

    @staticmethod
    def get_org_zones(org_id):
        return Zone.query.filter_by(organizationId=org_id).all()

geofence_service = GeofenceService()
