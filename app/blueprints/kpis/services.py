from app.models.kpi import AdvancedVehicleKPI
from app.models.vehicle import Vehicle
from app.extensions import db
from sqlalchemy import func

class KPIService:
    @staticmethod
    def get_dashboard_stats(org_id):
        # Resumen básico de la organización
        summary = AdvancedVehicleKPI.query.filter_by(organizationId=org_id).first()
        
        # Conteo de vehículos
        vehicle_count = Vehicle.query.filter_by(organizationId=org_id).count()
        
        return {
            "total_vehicles": vehicle_count,
            "avg_speed": float(summary.velocidadPromedio) if summary and summary.velocidadPromedio else 0,
            "total_distance": float(summary.distanciaRecorrida) if summary and summary.distanciaRecorrida else 0,
            "critical_events": summary.eventosCriticos if summary else 0,
            "fuel_consumption": float(summary.consumoCombustible) if summary and summary.consumoCombustible else 0
        }

    @staticmethod
    def get_activity_chart(org_id):
        # Placeholder para datos de gráfico de actividad
        return {
            "labels": ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"],
            "values": [0, 0, 0, 0, 0, 0, 0]
        }

    @staticmethod
    def get_fleet_distribution(org_id):
        # Distribución básica por tipo de vehículo
        results = db.session.query(
            Vehicle.type, func.count(Vehicle.id)
        ).filter_by(organizationId=org_id).group_by(Vehicle.type).all()
        
        return {str(t): count for t, count in results}

    @staticmethod
    def get_org_summary(org_id, start_date=None, end_date=None):
        return AdvancedVehicleKPI.query.filter_by(organizationId=org_id).first()

    @staticmethod
    def get_rankings(org_id):
        return []

kpi_service = KPIService()
