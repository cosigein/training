from app.models.vehicle import Vehicle, Fleet
from app.extensions import db

class VehicleService:
    @staticmethod
    def get_org_vehicles(org_id):
        return Vehicle.query.filter_by(organizationId=org_id).all()

    @staticmethod
    def get_vehicle(vehicle_id, org_id):
        return Vehicle.query.filter_by(id=vehicle_id, organizationId=org_id).first()

    @staticmethod
    def create_vehicle(data, org_id):
        vehicle = Vehicle(
            name=data["name"],
            model=data.get("model"),
            licensePlate=data["licensePlate"],
            brand=data.get("brand"),
            identifier=data["identifier"],
            type=data.get("type", "CAR"),
            organizationId=org_id,
            status=data.get("status", "ACTIVE")
        )
        db.session.add(vehicle)
        db.session.commit()
        return vehicle

    @staticmethod
    def update_vehicle(vehicle, data):
        vehicle.name = data.get("name", vehicle.name)
        vehicle.model = data.get("model", vehicle.model)
        vehicle.licensePlate = data.get("licensePlate", vehicle.licensePlate)
        vehicle.status = data.get("status", vehicle.status)
        db.session.commit()
        return vehicle

    @staticmethod
    def delete_vehicle(vehicle):
        # Soft delete is preferred in some systems, but let's do hard delete for now or check status
        vehicle.status = "DELETED"
        db.session.commit()
        return True

class FleetService:
    @staticmethod
    def get_org_fleets(org_id):
        return Fleet.query.filter_by(organizationId=org_id).all()

vehicle_service = VehicleService()
fleet_service = FleetService()
