from flask import jsonify, request, render_template
from . import vehicles_bp
from .services import vehicle_service, fleet_service
from app.utils.decorators import jwt_required, get_jwt_identity, require_role
from app.models.auth import User

@vehicles_bp.route("/", methods=["GET"])
@require_role(["ADMIN", "MANAGER"])
def list_vehicles():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    vehicles = vehicle_service.get_org_vehicles(user.organizationId)
    
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify([{
            "id": v.id,
            "name": v.name,
            "licensePlate": v.licensePlate,
            "model": v.model,
            "status": v.status
        } for v in vehicles])
        
    return render_template("vehicles/list.html", vehicles=vehicles)

@vehicles_bp.route("/<string:id>", methods=["GET"])
@require_role(["ADMIN", "MANAGER"])
def get_vehicle_detail(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    vehicle = vehicle_service.get_vehicle(id, user.organizationId)
    
    if not vehicle:
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({"message": "Vehículo no encontrado"}), 404
        return render_template("errors/404.html"), 404
        
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({
            "id": vehicle.id,
            "name": vehicle.name,
            "licensePlate": vehicle.licensePlate,
            "model": vehicle.model,
            "identifier": vehicle.identifier,
            "status": vehicle.status
        })

    # For the template, we might want recent sessions
    from app.blueprints.sessions.services import session_service
    sessions = session_service.get_org_sessions(user.organizationId, vehicle_id=vehicle.id)
        
    return render_template("vehicles/detail.html", vehicle=vehicle, sessions=sessions)

@vehicles_bp.route("/", methods=["POST"])
@require_role(["ADMIN"])
def create_vehicle():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()
    
    if not data or not data.get("name") or not data.get("licensePlate") or not data.get("identifier"):
        return jsonify({"message": "Faltan datos obligatorios"}), 400
        
    vehicle = vehicle_service.create_vehicle(data, user.organizationId)
    return jsonify({"message": "Vehículo creado", "id": vehicle.id}), 201

@vehicles_bp.route("/fleets", methods=["GET"])
@require_role(["ADMIN", "MANAGER"])
def list_fleets():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    fleets = fleet_service.get_org_fleets(user.organizationId)
    
    return jsonify([{
        "id": f.id,
        "name": f.name
    } for f in fleets])
