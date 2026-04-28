from flask import jsonify, request
from . import telemetry_bp
from app.utils.decorators import jwt_required, get_jwt_identity, require_role
from app.models.auth import User

@telemetry_bp.route("/live", methods=["GET"])
@require_role(["ADMIN"])
def get_live_data():
    # Placeholder for live data polling or streaming info
    return jsonify({"status": "streaming_active", "connections": 0})
