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
    # Sync Webfleet de attempts cerrados sin sync (D-WF-001).
    # Cada 10 minutos por defecto — configurable con WEBFLEET_SYNC_INTERVAL_MIN.
    "webfleet-sync-recent": {
        "task": "training.webfleet_sync_recent",
        "schedule": crontab(minute="*/10"),
    },
    # Actualización de flota en vivo desde Webfleet — posición, estado, odómetro…
    "webfleet-sync-vehicles": {
        "task": "training.sync_vehicles",
        "schedule": crontab(minute="*/10"),
    },
}
