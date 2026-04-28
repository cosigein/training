from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_compress import Compress
from flask_caching import Cache
from flask_talisman import Talisman
from flask_babel import Babel
from celery import Celery

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
cors = CORS()
compress = Compress()
cache = Cache()
talisman = Talisman()
babel = Babel()

def create_celery_app(app=None):
    celery = Celery(
        app.import_name if app else "doback_celery",
        broker=app.config["CELERY_BROKER_URL"] if app else "redis://localhost:6379/0"
    )
    if app:
        celery.conf.update(app.config)
        
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    return celery
