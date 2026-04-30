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

config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
