"""Fixtures globales de pytest.

Notas:
- TestingConfig apunta por default a `DATABASE_URL_TEST`. Si esa BD no está creada (caso
  típico en local), antes de `create_app` reescribimos la env var apuntando a la dev DB
  para que los integration tests read-only del blueprint `mobile_api` corran sin que el
  dev tenga que crear/sembrar una BD test propia.
- TODO Joel: cuando montés CI, definí `DATABASE_URL_TEST` con BD test sembrada propia y
  el fallback no se dispara. Esto deja de ser hack.
"""

import os

import pytest
from dotenv import load_dotenv

# Cargar .env antes de cualquier inspección de env vars (igual que app.config).
load_dotenv()


def _ensure_db_url():
    """Si DATABASE_URL_TEST no es alcanzable, fallback a DATABASE_URL.

    Tiene que correr ANTES de `create_app` para que SQLAlchemy bind a la URL correcta.
    """
    test_url = os.environ.get("DATABASE_URL_TEST", "")
    dev_url = os.environ.get("DATABASE_URL", "")
    if not test_url or not dev_url or test_url == dev_url:
        return

    try:
        from sqlalchemy import create_engine

        engine = create_engine(test_url)
        engine.connect().close()
    except Exception:
        os.environ["DATABASE_URL_TEST"] = dev_url


@pytest.fixture(scope="session")
def app():
    _ensure_db_url()
    from app import create_app
    from app.extensions import db as _db

    application = create_app("testing")
    application.config["TESTING"] = True
    return application


@pytest.fixture(scope="session")
def db(app):
    from app.extensions import db as _db

    with app.app_context():
        yield _db


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers_for(app):
    """Factory: `auth_headers_for(user_id)` → dict con Authorization Bearer."""
    from flask_jwt_extended import create_access_token

    def _make(user_id):
        with app.app_context():
            token = create_access_token(identity=user_id)
        return {"Authorization": f"Bearer {token}"}

    return _make
