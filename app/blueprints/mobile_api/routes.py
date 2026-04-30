from datetime import datetime, timezone

from flask import jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)

from app.blueprints.auth.services import auth_service
from app.blueprints.manager.ranking_service import get_ranking
from app.blueprints.mobile_api import mobile_api_bp
from app.blueprints.mobile_api.errors import error_response
from app.blueprints.mobile_api.schemas import (
    ConvocatoriaSummarySchema,
    StandingSchema,
    UserSchema,
)
from app.blueprints.mobile_api.services import (
    convocatorias_for_user,
    get_convocatoria_detail,
)
from app.extensions import limiter
from app.models.auth import User, UserRole
from app.models.training import Enrollment, EnrollmentStatus
from app.utils.decorators import require_role


def _current_user_or_401():
    user_id = get_jwt_identity()
    if not user_id:
        return None, error_response(401, "unauthenticated", "Token sin identidad")
    user = User.query.get(user_id)
    if not user:
        return None, error_response(401, "unauthenticated", "Usuario no encontrado")
    return user, None


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


@mobile_api_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user, err = _current_user_or_401()
    if err is not None:
        return err
    return jsonify(UserSchema().dump(user)), 200


@mobile_api_bp.route("/me/convocatorias", methods=["GET"])
@jwt_required()
def me_convocatorias():
    user, err = _current_user_or_401()
    if err is not None:
        return err
    items = convocatorias_for_user(user)
    schema = ConvocatoriaSummarySchema(many=True)
    return jsonify({"items": schema.dump(items)}), 200


@mobile_api_bp.route("/me/convocatorias/<string:conv_id>/standing", methods=["GET"])
@require_role([UserRole.STUDENT.value])
def me_standing(conv_id):
    user, err = _current_user_or_401()
    if err is not None:
        return err

    enrollment = (
        Enrollment.query
        .filter_by(
            convocatoriaId=conv_id,
            studentId=user.id,
            organizationId=user.organizationId,
        )
        .filter(Enrollment.status != EnrollmentStatus.INVALIDATED)
        .first()
    )
    if not enrollment:
        # 404, no 403 — no leakeamos existencia de la convocatoria
        return error_response(404, "not_found", "No estás inscripto en esa convocatoria")

    conv_dict, entries = get_ranking(conv_id, user.organizationId)
    if not conv_dict:
        return error_response(404, "not_found", "Convocatoria no encontrada")

    my_entry = next(
        (e for e in entries if e.get("candidato", {}).get("id") == user.id),
        None,
    )
    if not my_entry:
        return error_response(404, "not_found", "Sin posición en el ranking")

    standing = {
        "convocatoriaId": conv_id,
        "position": my_entry["puesto"],
        "totalCandidates": len(entries),
        "plazas": conv_dict["plazas"],
        "score": my_entry["nota_media"],
        "attemptsCompleted": my_entry["rutas_completadas"],
        "attemptsTotal": my_entry["rutas_total"],
        "status": enrollment.status.value,
    }
    return jsonify(StandingSchema().dump(standing)), 200


_ADMIN_ROLES = [
    UserRole.MANAGER.value,
    UserRole.ADMIN.value,
    UserRole.SUPER_ADMIN.value,
]


@mobile_api_bp.route("/convocatorias", methods=["GET"])
@require_role(_ADMIN_ROLES)
def list_convocatorias():
    user, err = _current_user_or_401()
    if err is not None:
        return err
    items = convocatorias_for_user(user)
    schema = ConvocatoriaSummarySchema(many=True)
    return jsonify({"items": schema.dump(items)}), 200


@mobile_api_bp.route("/convocatorias/<string:conv_id>", methods=["GET"])
@require_role(_ADMIN_ROLES)
def convocatoria_detail(conv_id):
    user, err = _current_user_or_401()
    if err is not None:
        return err
    detail = get_convocatoria_detail(conv_id, user)
    if not detail:
        return error_response(404, "not_found", "Convocatoria no encontrada")
    return jsonify(ConvocatoriaSummarySchema().dump(detail)), 200
