import os
from flask import render_template, jsonify, request, redirect, url_for, current_app, send_from_directory
from app.extensions import db
from app.utils.decorators import jwt_required, get_jwt_identity, require_role
from app.models.auth import User
import time
from . import system_bp

@system_bp.route("/", methods=["GET"])
def index():
    return redirect(url_for('sessions.list_attempts'))

@system_bp.route("/settings", methods=["GET", "POST"])
@require_role(["ADMIN", "MANAGER"])
def settings():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if request.method == "POST":
        # Lógica para actualizar configuración en el futuro
        pass
        
    return render_template("settings.html", user=user)

@system_bp.route("/health", methods=["GET"])
def health_check():
    try:
        # Check database
        db.session.execute(db.text("SELECT 1"))
        return jsonify({
            "status": "UP",
            "database": "CONNECTED",
            "timestamp": time.time()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "DOWN",
            "database": "DISCONNECTED",
            "error": str(e)
        }), 500

@system_bp.route("/status", methods=["GET"])
def system_status():
    return jsonify({
        "version": "3.0.0-flask",
        "environment": "development",
        "uptime": "not_implemented"
    })
