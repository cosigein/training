from functools import wraps
from flask import jsonify, request, redirect, url_for, flash
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models.auth import User


def _wants_json():
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


def require_role(roles):
    if isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)

            if not user:
                if _wants_json():
                    return jsonify({"message": "Usuario no encontrado"}), 404
                return redirect(url_for('auth.login'))

            if not user.organizationId:
                if _wants_json():
                    return jsonify({"message": "Organización no vinculada"}), 403
                flash("Tu cuenta no tiene una organización vinculada.", "warning")
                return redirect(url_for('auth.login'))

            user_role = user.role.value if hasattr(user.role, 'value') else user.role
            if user_role not in roles:
                if _wants_json():
                    return jsonify({"message": "Permisos insuficientes"}), 403
                flash("No tenés permisos para acceder a esa sección.", "warning")
                return redirect(url_for('kpis.dashboard_executive'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_org(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or not user.organizationId:
            return jsonify({"message": "Organización no vinculada"}), 403

        return f(*args, **kwargs)
    return decorated_function
