import os
from app import create_app
from app.extensions import db
from app.models.geofence import Geofence, GeofenceType, GeofenceMode
from app.models.auth import Organization

app = create_app()

def seed_geofences():
    with app.app_context():
        org = Organization.query.first()
        if not org:
            print("No organization found. Please run setup_db.py first.")
            return

        # Clear existing geofences for this org (test mode)
        # Geofence.query.filter_by(organizationId=org.id).delete()
        
        # Center: 37.907, -4.729 (Córdoba area)
        
        # 1. Base Operativa (Polygon)
        base_geo = {
            "type": "Polygon",
            "coordinates": [[
                [-4.732, 37.905],
                [-4.726, 37.905],
                [-4.726, 37.910],
                [-4.732, 37.910],
                [-4.732, 37.905]
            ]]
        }
        
        if not Geofence.query.filter_by(name="Base Central Córdoba").first():
            gf1 = Geofence(
                name="Base Central Córdoba",
                description="Zona de carga y descanso principal",
                type=GeofenceType.POLYGON,
                mode=GeofenceMode.TRUCK,
                geometry=base_geo,
                organizationId=org.id
            )
            db.session.add(gf1)

        # 2. Zona Restringida - Centro Urbano (Polygon)
        urb_geo = {
            "type": "Polygon",
            "coordinates": [[
                [-4.785, 37.880],
                [-4.760, 37.880],
                [-4.760, 37.900],
                [-4.785, 37.900],
                [-4.785, 37.880]
            ]]
        }
        
        if not Geofence.query.filter_by(name="Casco Histórico").first():
            gf2 = Geofence(
                name="Casco Histórico",
                description="Acceso restringido a vehículos pesados",
                type=GeofenceType.POLYGON,
                mode=GeofenceMode.TRUCK,
                geometry=urb_geo,
                enabled=True,
                organizationId=org.id
            )
            db.session.add(gf2)

        # 3. Punto de Control - Av. Brillante (Circle/Point simulation if needed)
        # Leaflet handles circle as a point + radius, but we use Polygon for everything for now or Circle type
        # For simplicity, another polygon
        control_geo = {
            "type": "Polygon",
            "coordinates": [[
                [-4.730, 37.915],
                [-4.725, 37.915],
                [-4.725, 37.920],
                [-4.730, 37.920],
                [-4.730, 37.915]
            ]]
        }
        
        if not Geofence.query.filter_by(name="Control Norte").first():
            gf3 = Geofence(
                name="Control Norte",
                description="Punto de control de salida norte",
                type=GeofenceType.POLYGON,
                mode=GeofenceMode.TRUCK,
                geometry=control_geo,
                organizationId=org.id
            )
            db.session.add(gf3)

        db.session.commit()
        print("✅ Geofences seeded successfully!")

if __name__ == "__main__":
    seed_geofences()
