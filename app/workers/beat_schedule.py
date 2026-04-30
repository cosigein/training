"""
Configuración del beat schedule de Celery (T9).

Se aplica en celery_worker.py via celery.conf.beat_schedule.
"""
from celery.schedules import crontab

BEAT_SCHEDULE = {
    # Ranking provisional diario — 06:00 Europe/Madrid
    "ranking-diario-06h": {
        "task": "training.compute_daily_rankings",
        "schedule": crontab(hour=6, minute=0),
        "options": {"timezone": "Europe/Madrid"},
    },
    # Transición CLOSED → LOCKED cada 15 min
    "lock-closed-convocatorias": {
        "task": "training.lock_closed_convocatorias",
        "schedule": crontab(minute="*/15"),
    },
}
