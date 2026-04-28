from flask import jsonify, request, render_template
from . import geofences_bp
from .services import geofence_service
from app.utils.decorators import jwt_required, get_jwt_identity, require_org
from app.models.auth import User
from app.models.vehicle import Vehicle, RealtimePosition

@geofences_bp.route("/", methods=["GET"])
@require_org
def list_geofences():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    geofences = geofence_service.get_org_geofences(user.organizationId)
    
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify([{
            "id": g.id,
            "name": g.name,
            "type": g.type.value if hasattr(g.type, 'value') else g.type,
            "enabled": g.enabled
        } for g in geofences])
        
    # Format for Leaflet (GeoJSON)
    geofences_json = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"id": g.id, "name": g.name},
            "geometry": g.geometry
        } for g in geofences]
    }
    
    # Fetch realtime positions
    vehicles_data = []
    positions = RealtimePosition.query.join(Vehicle).filter(Vehicle.organizationId == user.organizationId).all()
    for p in positions:
        vehicles_data.append({
            "id": p.vehicleId,
            "name": p.vehicle.name,
            "lat": p.lat,
            "lon": p.lon,
            "speed": p.speed,
            "timestamp": p.timestamp.strftime('%H:%M:%S')
        })
        
    return render_template("geofences/list.html", 
                         geofences=geofences, 
                         geofences_json=geofences_json,
                         vehicles_json=vehicles_data)

@geofences_bp.route("/parks", methods=["GET"])
@require_org
def list_parks():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    parks = geofence_service.get_org_parks(user.organizationId)
    
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "identifier": p.identifier
    } for p in parks])

@geofences_bp.route("/zones", methods=["GET"])
@require_org
def list_zones():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    zones = geofence_service.get_org_zones(user.organizationId)
    
    return jsonify([{
        "id": z.id,
        "name": z.name,
        "type": z.type
    } for z in zones])
