import os
import time
import warnings
# Silenciar advertencias de Eventlet y Limiter para un arranque limpio
warnings.filterwarnings("ignore", message="Eventlet is deprecated")
warnings.filterwarnings("ignore", category=UserWarning, module="flask_limiter")

from flask import Flask, g, request
from loguru import logger
from app.config import config
from app.extensions import (
    db, migrate, jwt, socketio, login_manager,
    csrf, limiter, cors, compress, cache, talisman,
    babel, create_celery_app, init_loguru,
)


def _init_sentry(app) -> None:
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    sentry_sdk.init(
        dsn=dsn,
        integrations=[FlaskIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment=os.getenv("FLASK_ENV", "development"),
        release=os.getenv("APP_VERSION", "training@dev"),
    )

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    _init_sentry(app)
    
    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mq = app.config.get("REDIS_URL") if not app.debug else None
    socketio.init_app(app, message_queue=mq, cors_allowed_origins="*")
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    cors.init_app(app)
    compress.init_app(app)
    cache.init_app(app)
    # Talisman se suele activar solo en producción por CSP.
    # CSP pragmática: permite los CDNs que usa la UI (Google Fonts, Phosphor,
    # Leaflet, tiles cartocdn) y `unsafe-inline` para los estilos/scripts inline
    # que aún tienen los templates. Endurecer post-demo migrando inline a archivos.
    if not app.debug and not app.testing:
        csp = {
            "default-src": "'self'",
            "style-src":   ["'self'", "'unsafe-inline'",
                            "https://fonts.googleapis.com",
                            "https://unpkg.com",
                            "https://cdn.jsdelivr.net"],
            "font-src":    ["'self'",
                            "https://fonts.gstatic.com",
                            "https://unpkg.com",
                            "https://cdn.jsdelivr.net"],
            "script-src":  ["'self'", "'unsafe-inline'",
                            "https://unpkg.com",
                            "https://cdn.jsdelivr.net"],
            "img-src":     ["'self'", "data:",
                            "https://*.basemaps.cartocdn.com",
                            "https://unpkg.com",
                            "https://cdn.jsdelivr.net"],
            "connect-src": ["'self'",
                            "https://unpkg.com",
                            "https://cdn.jsdelivr.net"],
            "frame-ancestors": "'none'",
        }
        talisman.init_app(
            app,
            content_security_policy=csp,
            force_https=False,
            strict_transport_security=True,
        )
    babel.init_app(app)
    init_loguru(app)

    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.vehicles import vehicles_bp
    from app.blueprints.sessions import sessions_bp
    from app.blueprints.events import events_bp
    from app.blueprints.uploads import uploads_bp
    from app.blueprints.system import system_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.manager import manager_bp
    from app.blueprints.kiosko import kiosko_bp
    from app.blueprints.student import student_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(vehicles_bp, url_prefix="/vehicles")
    app.register_blueprint(sessions_bp, url_prefix="/sessions")
    app.register_blueprint(events_bp, url_prefix="/events")
    app.register_blueprint(uploads_bp, url_prefix="/uploads")
    app.register_blueprint(system_bp, url_prefix="/")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(manager_bp, url_prefix="/manager")
    app.register_blueprint(kiosko_bp, url_prefix="/kiosko")
    app.register_blueprint(student_bp, url_prefix="/alumno")

    # JWT en header (no cookie) → no necesita CSRF
    from app.blueprints.mobile_api import mobile_api_bp
    app.register_blueprint(mobile_api_bp)
    csrf.exempt(mobile_api_bp)

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

    @app.before_request
    def _start_timer():
        g._t0 = time.time()

    @app.after_request
    def _log_request(response):
        duration_ms = int((time.time() - getattr(g, "_t0", time.time())) * 1000)
        logger.info(
            "request_handled method={} path={} status={} duration_ms={}",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response

    # Scheduler en proceso: cron de ranking y lock de convocatorias (T9)
    # No arrancar en testing para no interferir con los tests
    if not app.config.get("TESTING"):
        from app.scheduler import init_scheduler
        init_scheduler(app)

    return app
