from flask import jsonify, request, render_template
from . import events_bp
from .services import event_service
from app.utils.decorators import jwt_required, get_jwt_identity, require_org
from app.models.auth import User

@events_bp.route("/", methods=["GET"])
@require_org
def list_events():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    limit = request.args.get("limit", 100, type=int)
    events = event_service.get_org_events(user.organizationId, limit)
    
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify([{
            "id": e.id,
            "type": e.type,
            "name": e.name,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "severity": e.severity,
            "status": e.status,
            "vehicleId": e.vehicleId
        } for e in events])
        
    return render_template("events/list.html", events=events)

@events_bp.route("/<string:id>/acknowledge", methods=["POST"])
@require_org
def acknowledge_event(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    event = event_service.get_event(id, user.organizationId)
    
    if not event:
        return jsonify({"message": "Evento no encontrado"}), 404
        
    event_service.acknowledge_event(event, user_id)
    return jsonify({"message": "Evento reconocido", "status": "ACKNOWLEDGED"})

@events_bp.route("/<string:event_id>", methods=["GET"])
@require_org
def get_event_detail(event_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    event = event_service.get_event(event_id, user.organizationId)
    
    if not event:
        return render_template("errors/404.html"), 404
        
    return render_template("events/detail.html", event=event)
