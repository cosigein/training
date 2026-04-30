from flask import jsonify, redirect, url_for, request, flash
from flask_jwt_extended import unset_jwt_cookies


def _wants_json():
    """True for API/AJAX clients, False for browsers (so they get redirected)."""
    # /api/* es siempre JSON — clientes nativos no negocian Accept ni mandan is_json
    if request.path.startswith("/api/"):
        return True
    if request.is_json:
        return True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return True
    accept = request.headers.get('Accept', '')
    if 'text/html' in accept:
        return False
    if 'application/json' in accept:
        return True
    return False


def init_jwt_handlers(jwt):
    @jwt.expired_token_loader
    def _expired(jwt_header, jwt_payload):
        if _wants_json():
            return jsonify({"message": "Token expirado", "error": "token_expired"}), 401
        flash("Tu sesión ha expirado. Iniciá sesión de nuevo.", "warning")
        response = redirect(url_for('auth.login'))
        unset_jwt_cookies(response)
        return response

    @jwt.invalid_token_loader
    def _invalid(reason):
        if _wants_json():
            return jsonify({"message": "Token inválido", "error": "token_invalid", "reason": reason}), 401
        flash("Tu sesión es inválida. Iniciá sesión de nuevo.", "warning")
        response = redirect(url_for('auth.login'))
        unset_jwt_cookies(response)
        return response

    @jwt.unauthorized_loader
    def _missing(reason):
        if _wants_json():
            return jsonify({"message": "No autenticado", "error": "no_token", "reason": reason}), 401
        return redirect(url_for('auth.login'))
