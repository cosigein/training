from app import create_app
from app.extensions import create_celery_app

flask_app = create_app()
celery = create_celery_app(flask_app)
