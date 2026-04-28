from flask import jsonify, request, render_template
from . import sessions_bp
from .services import session_service
from app.utils.decorators import jwt_required, get_jwt_identity, require_org
from app.models.auth import User

@sessions_bp.route("/", methods=["GET"])
@require_org
def list_sessions():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    limit = request.args.get("limit", 50, type=int)
    sessions = session_service.get_org_sessions(user.organizationId, limit)
    
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify([{
            "id": s.id,
            "startTime": s.startTime.isoformat() if s.startTime else None,
            "endTime": s.endTime.isoformat() if s.endTime else None,
            "vehicleId": s.vehicleId,
            "status": s.status,
            "type": s.type
        } for s in sessions])
        
    return render_template("sessions/list.html", sessions=sessions)

@sessions_bp.route("/<string:id>", methods=["GET"])
@require_org
def get_session_detail(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    session = session_service.get_session_details(id, user.organizationId)
    
    if not session:
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({"message": "Sesión no encontrada"}), 404
        return render_template("errors/404.html"), 404
        
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({
            "id": session.id,
            "startTime": session.startTime.isoformat() if session.startTime else None,
            "endTime": session.endTime.isoformat() if session.endTime else None,
            "vehicleId": session.vehicleId,
            "status": session.status,
            "summary": session.meta_data
        })

    # For the template, we want events and GPS
    events = session_service.get_session_events(id)
    gps_data = session_service.get_session_gps(id)
    
    # Format GPS for GeoJSON
    route_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[g.longitude, g.latitude] for g in gps_data]
        }
    }

    # Chart data
    chart_data = {
        "labels": [g.timestamp.strftime("%H:%M:%S") for g in gps_data],
        "speed": [g.speed for g in gps_data],
        "rpm": [g.rpm if hasattr(g, 'rpm') else 0 for g in gps_data] # RPM might not be in GPS model
    }
        
    return render_template("sessions/detail.html", session=session, events=events, route_geojson=route_geojson, chart_data=chart_data)

@sessions_bp.route("/<string:id>", methods=["DELETE"])
@require_org
def delete_session(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    deleted = session_service.delete_session(id, user.organizationId)
    if not deleted:
        return jsonify({"message": "Sesión no encontrada"}), 404
    return "", 204

@sessions_bp.route("/<string:id>/gps", methods=["GET"])
@require_org
def get_session_gps(id):
    # Validar que la sesión pertenece a la org del usuario (podría hacerse en service)
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    session = session_service.get_session_details(id, user.organizationId)
    
    if not session:
        return jsonify({"message": "Sesión no encontrada"}), 404
        
    gps_data = session_service.get_session_gps(id)
    return jsonify([{
        "lat": g.latitude,
        "lon": g.longitude,
        "speed": g.speed,
        "timestamp": g.timestamp.isoformat()
    } for g in gps_data])
