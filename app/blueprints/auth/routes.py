from flask import request, jsonify, make_response, render_template, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, current_user
from flask_jwt_extended import (
    set_access_cookies, set_refresh_cookies, 
    unset_jwt_cookies, jwt_required, get_jwt_identity,
    create_access_token, create_refresh_token
)
from . import auth_bp
from .services import auth_service
from app.models.auth import User, UserRole
from app.models.training import RfidCard, Enrollment, Convocatoria, ConvocatoriaStatus
from app.blueprints.kiosko.services import get_plaza_for_student


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Support both JSON and Form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
            
        if not data or not data.get("email") or not data.get("password"):
            if request.is_json:
                return jsonify({"message": "Faltan credenciales"}), 400
            flash("Faltan credenciales", "danger")
            return render_template("auth/login.html")
        
        user = auth_service.authenticate_user(data["email"], data["password"])
        if not user:
            if request.is_json:
                return jsonify({"message": "Credenciales inválidas"}), 401
            flash("Credenciales inválidas", "danger")
            return render_template("auth/login.html")
        
        access_token, refresh_token = auth_service.get_user_tokens(user)
        
        # Log in for flask-login (session based current_user)
        login_user(user)
        
        if request.is_json:
            response = jsonify({
                "message": "Login exitoso",
                "user": {"id": user.id, "email": user.email, "name": user.name}
            })
        else:
            role = user.role.value if hasattr(user.role, 'value') else user.role
            if role == "STUDENT":
                dest = url_for('student.dashboard')
            elif role in ("ADMIN", "SUPER_ADMIN"):
                dest = url_for('admin.dashboard')
            elif role == "MANAGER":
                dest = url_for('manager.dashboard')
            else:
                dest = url_for('sessions.list_attempts')
            response = redirect(dest)
        
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        return response
        
    return render_template("auth/login.html")
    
@auth_bp.route("/login-rfid", methods=["POST"])
def login_rfid():
    """Autentica a un usuario mediante su UID de tarjeta RFID."""
    data = request.get_json(silent=True) or request.form
    rfid_uid = data.get("rfid_uid")
    
    if not rfid_uid:
        if request.is_json:
            return jsonify({"message": "UID de tarjeta no proporcionado"}), 400
        flash("UID de tarjeta no proporcionado", "danger")
        return redirect(url_for('auth.login'))

    # Buscar tarjeta activa y no revocada
    card = RfidCard.query.filter_by(uid=rfid_uid, active=True).filter(RfidCard.revokedAt.is_(None)).first()
    
    if not card or not card.assignedTo:
        if current_app.config.get('DEBUG'):
             print(f"DEBUG: Intento de login con UID {rfid_uid} no encontrado en DB.")
        
        if request.is_json:
            return jsonify({"message": "Tarjeta no reconocida o no asignada"}), 401
        flash("Tarjeta RFID no reconocida o no asignada a ningún usuario.", "danger")
        return redirect(url_for('auth.login'))
        
    user = User.query.get(card.assignedTo)

    if not user:
        if request.is_json:
            return jsonify({"message": "Usuario no encontrado"}), 404
        flash("Usuario asociado a la tarjeta no encontrado.", "danger")
        return redirect(url_for('auth.login'))

    # ── RESTRICCIÓN DE ROL: Solo estudiantes pueden entrar vía RFID ──
    role = user.role.value if hasattr(user.role, 'value') else user.role
    if role != "STUDENT":
        flash("El acceso por RFID está restringido exclusivamente a estudiantes.", "warning")
        return redirect(url_for('auth.login'))
        
    access_token, refresh_token = auth_service.get_user_tokens(user)
    login_user(user)
    
    # Redirigir al Kiosko si tiene plaza (en cualquier convocatoria abierta)
    plaza, conv_id = get_plaza_for_student(user.id)
    if plaza:
        dest = url_for('kiosko.rutas', plaza=plaza, convocatoria=conv_id)
    else:
        # Fallback si es estudiante pero no está en ninguna convocatoria OPEN con plaza
        dest = url_for('student.dashboard')
        
    if request.is_json:
        response = jsonify({
            "message": "Login RFID exitoso",
            "redirect": dest,
            "user": {"id": user.id, "name": user.name}
        })
    else:
        response = redirect(dest)
        set_access_cookies(response, access_token)
        set_refresh_cookies(response, refresh_token)
        return response



    
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Support both JSON and Form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
            
        if not data or not data.get("email") or not data.get("password") or not data.get("name"):
            if request.is_json:
                return jsonify({"message": "Faltan datos obligatorios"}), 400
            flash("Faltan datos obligatorios", "danger")
            return render_template("auth/register.html")
            
        user, error = auth_service.register_user(
            email=data["email"],
            password=data["password"],
            name=data["name"],
            role=data.get("role", "VIEWER")
        )
        
        if error:
            if request.is_json:
                return jsonify({"message": error}), 400
            flash(error, "danger")
            return render_template("auth/register.html")
            
        if request.is_json:
            return jsonify({
                "message": "Usuario creado correctamente",
                "user": {"id": user.id, "email": user.email}
            }), 201

        flash("Cuenta creada correctamente. Por favor, inicie sesión.", "success")
        return redirect(url_for('auth.login'))

    return render_template("auth/register.html")
        
@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    logout_user()  # Importante: limpia la sesión de flask-login
    response = redirect(url_for('auth.login'))
    unset_jwt_cookies(response)
    return response

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "Usuario no encontrado"}), 404
        
    return jsonify({
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value if hasattr(user.role, 'value') else user.role,
        "organizationId": user.organizationId
    })

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = auth_service.create_access_token(identity=user_id)
    response = jsonify({"message": "Token renovado"})
    set_access_cookies(response, access_token)
    return response
