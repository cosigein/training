from flask import jsonify, request, render_template
from . import admin_bp
from .services import admin_service
from app.utils.decorators import jwt_required, get_jwt_identity, require_org, require_role
from app.models.auth import User

@admin_bp.route("/users", methods=["GET"])
@require_role(["ADMIN"])
@require_org
def list_users():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Si es ADMIN global podría ver todo, pero por ahora limitamos a su org
    users = admin_service.get_all_users(user.organizationId)
    
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify([{
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "role": u.role.value if hasattr(u.role, 'value') else u.role,
            "status": u.status
        } for u in users])
        
    return render_template("admin/organizations.html", users=users) # Simplified reuse for users too

@admin_bp.route("/organizations", methods=["GET"])
@require_role(["ADMIN"])
def list_organizations():
    # Este endpoint debería ser solo para superadmins reales
    orgs = admin_service.get_all_organizations()
    
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify([{
            "id": o.id,
            "name": o.name,
            "createdAt": o.createdAt.isoformat()
        } for o in orgs])
        
    return render_template("admin/organizations.html", organizations=orgs)
