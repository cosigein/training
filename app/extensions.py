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


import logging
import sys
from loguru import logger as loguru_logger


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def init_loguru(app) -> None:
    loguru_logger.remove()
    loguru_logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        serialize=app.config.get("LOGURU_JSON", not app.debug),
    )
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)
    app.logger.handlers = [InterceptHandler()]
    app.logger.propagate = False
    for noisy in ("werkzeug", "sqlalchemy.engine", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
