import os
import warnings
# Silenciar advertencias de Eventlet y Limiter para un arranque limpio
warnings.filterwarnings("ignore", message="Eventlet is deprecated")
warnings.filterwarnings("ignore", category=UserWarning, module="flask_limiter")

from flask import Flask
from app.config import config
from app.extensions import (
    db, migrate, jwt, socketio, login_manager, 
    csrf, limiter, cors, compress, cache, talisman, 
    babel, create_celery_app
)

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "default")
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    socketio.init_app(app, message_queue=app.config.get("REDIS_URL"), cors_allowed_origins="*")
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    cors.init_app(app)
    compress.init_app(app)
    cache.init_app(app)
    # Talisman se suele activar solo en producción por CSP
    if not app.debug:
        talisman.init_app(app)
    babel.init_app(app)
    
    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.vehicles import vehicles_bp
    from app.blueprints.sessions import sessions_bp
    from app.blueprints.events import events_bp
    from app.blueprints.geofences import geofences_bp
    from app.blueprints.uploads import uploads_bp
    from app.blueprints.kpis import kpis_bp
    from app.blueprints.system import system_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.reports import reports_bp
    from app.blueprints.telemetry import telemetry_bp
    
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(vehicles_bp, url_prefix="/vehicles")
    app.register_blueprint(sessions_bp, url_prefix="/sessions")
    app.register_blueprint(events_bp, url_prefix="/events")
    app.register_blueprint(geofences_bp, url_prefix="/geofences")
    app.register_blueprint(uploads_bp, url_prefix="/uploads")
    app.register_blueprint(kpis_bp, url_prefix="/kpis")
    app.register_blueprint(system_bp, url_prefix="/")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(telemetry_bp, url_prefix="/telemetry")
    
    # Custom Filters
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%d/%m/%Y %H:%M'):
        if value is None: return ""
        return value.strftime(format)

    @app.template_filter('durationformat')
    def durationformat(seconds):
        if not seconds: return "-"
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f'{int(hours)}h {int(minutes)}m'
        return f'{int(minutes)}m {int(seconds)}s'
    
    # Import models to ensure they are registered with SQLAlchemy
    from app import models
    from app.models.auth import User
    from app.middleware.audit import init_audit_context
    from app.middleware.jwt_handlers import init_jwt_handlers
    init_audit_context(app)
    init_jwt_handlers(jwt)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    return app
