from flask import jsonify
from werkzeug.exceptions import HTTPException

from app.blueprints.mobile_api import mobile_api_bp


def error_response(code, error_key, message, details=None, retry_after=None):
    body = {"error": error_key, "message": message}
    if details is not None:
        body["details"] = details
    response = jsonify(body)
    response.status_code = code
    if retry_after is not None:
        response.headers["Retry-After"] = str(retry_after)
    return response


@mobile_api_bp.errorhandler(400)
def _bad_request(_e):
    return error_response(400, "bad_request", "Solicitud inválida")


@mobile_api_bp.errorhandler(401)
def _unauthenticated(_e):
    return error_response(401, "unauthenticated", "Token ausente o inválido")


@mobile_api_bp.errorhandler(403)
def _forbidden(_e):
    return error_response(403, "forbidden", "No tenés permisos para este recurso")


@mobile_api_bp.errorhandler(404)
def _not_found(_e):
    return error_response(404, "not_found", "Recurso no encontrado")


@mobile_api_bp.errorhandler(422)
def _validation_error(e):
    details = None
    data = getattr(e, "data", None)
    if isinstance(data, dict):
        details = data.get("messages")
    return error_response(422, "validation_error", "Validación fallida", details=details)


@mobile_api_bp.errorhandler(429)
def _rate_limited(e):
    retry_after = getattr(e, "retry_after", None)
    return error_response(429, "rate_limited", "Has excedido el límite de peticiones", retry_after=retry_after)


@mobile_api_bp.errorhandler(HTTPException)
def _generic_http(e):
    code = e.code or 500
    if code >= 500:
        return error_response(code, "internal_error", "Error interno del servidor")
    return error_response(code, "http_error", e.description or str(e))
