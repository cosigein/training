from app import create_app
from app.extensions import create_celery_app

flask_app = create_app()
celery = create_celery_app(flask_app)

# Registrar tasks (shared_task se vincula al celery activo)
import app.workers.ranking_worker  # noqa: F401, E402
import app.workers.webfleet_worker  # noqa: F401, E402

# Beat schedule
from app.workers.beat_schedule import BEAT_SCHEDULE  # noqa: E402
celery.conf.beat_schedule = BEAT_SCHEDULE
celery.conf.timezone = "Europe/Madrid"
