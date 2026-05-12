import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "default-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["cookies", "headers"]
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = True
    # Separar el campo CSRF de JWT del de Flask-WTF para evitar conflicto.
    # Flask-WTF usa "csrf_token"; JWT-Extended usará "jwt_csrf_token".
    # El valor se inyecta vía JS desde el cookie csrf_access_token (no-httponly).
    JWT_ACCESS_CSRF_FIELD_NAME = "jwt_csrf_token"
    
    # Redis & Celery
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Babel
    BABEL_DEFAULT_LOCALE = "es"
    BABEL_SUPPORTED_LOCALES = ["es", "en"]
    
    # Limiter
    RATELIMIT_STORAGE_URI = os.environ.get("REDIS_URL", "memory://")
    
    # Cache
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL

    # Webfleet (D-WF-001 — integración con Webfleet.connect API).
    # Si WEBFLEET_ENABLED=false o faltan credenciales, el cliente entra en
    # modo MOCK: devuelve datos sintéticos de prueba. Útil para desarrollo y
    # demo sin acceso a la cuenta real de Bridgestone.
    WEBFLEET_ENABLED = os.environ.get("WEBFLEET_ENABLED", "false").lower() in ("true", "1", "yes")
    WEBFLEET_BASE_URL = os.environ.get("WEBFLEET_BASE_URL", "https://csv.webfleet.com/extern")
    WEBFLEET_ACCOUNT = os.environ.get("WEBFLEET_ACCOUNT", "")
    WEBFLEET_USERNAME = os.environ.get("WEBFLEET_USERNAME", "")
    WEBFLEET_PASSWORD = os.environ.get("WEBFLEET_PASSWORD", "")
    WEBFLEET_APIKEY = os.environ.get("WEBFLEET_APIKEY", "")
    # Cuota Webfleet de CMadrid: 14.400 req/día. Alertas a 70/85/95%.
    WEBFLEET_DAILY_QUOTA = int(os.environ.get("WEBFLEET_DAILY_QUOTA", "14400"))
    # Circuit breaker: tras N fallos consecutivos, abre por COOLDOWN segundos.
    WEBFLEET_CB_FAIL_THRESHOLD = int(os.environ.get("WEBFLEET_CB_FAIL_THRESHOLD", "3"))
    WEBFLEET_CB_COOLDOWN_S = int(os.environ.get("WEBFLEET_CB_COOLDOWN_S", "60"))
    # Sync periódico: cada N minutos busca attempts cerrados sin sync de las
    # últimas WEBFLEET_SYNC_LOOKBACK_H horas.
    WEBFLEET_SYNC_INTERVAL_MIN = int(os.environ.get("WEBFLEET_SYNC_INTERVAL_MIN", "10"))
    WEBFLEET_SYNC_LOOKBACK_H = int(os.environ.get("WEBFLEET_SYNC_LOOKBACK_H", "24"))

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://localhost/doback_dev")
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False

class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL_TEST", "postgresql://localhost/doback_test")
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False
    WTF_CSRF_ENABLED = False

class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    JWT_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"

class StagingConfig(BaseConfig):
    """Producción real pero sin HTTPS — VPS con HTTP directo en :4000."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = "Lax"

config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "staging": StagingConfig,
    "default": DevelopmentConfig
}
