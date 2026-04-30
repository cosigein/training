from datetime import datetime, timezone

from flask import jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from app.blueprints.auth.services import auth_service
from app.blueprints.mobile_api import mobile_api_bp
from app.blueprints.mobile_api.errors import error_response
from app.blueprints.mobile_api.schemas import UserSchema
from app.extensions import limiter


@mobile_api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "version": "v1",
        "time": datetime.now(timezone.utc).isoformat(),
    })


@mobile_api_bp.route("/auth/login", methods=["POST"])
@limiter.limit("10/minute")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return error_response(400, "bad_request", "Faltan credenciales")

    user = auth_service.authenticate_user(email, password)
    if not user:
        return error_response(401, "unauthenticated", "Credenciales inválidas")

    access_token, refresh_token = auth_service.get_user_tokens(user)
    user_dump = UserSchema().dump(user)
    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "user": user_dump,
    }), 200


@mobile_api_bp.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({
        "access_token": access_token,
        "expires_in": 3600,
    }), 200
