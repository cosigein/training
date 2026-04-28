from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models.auth import User

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
                return jsonify({"message": "Usuario no encontrado"}), 404
                
            user_role = user.role.value if hasattr(user.role, 'value') else user.role
            if user_role not in roles:
                return jsonify({"message": "Permisos insuficientes"}), 403
                
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
