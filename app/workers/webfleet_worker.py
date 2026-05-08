"""Worker periódico que sincroniza Attempts cerrados con Webfleet.

Lógica:
- Cada `WEBFLEET_SYNC_INTERVAL_MIN` (default 10) Celery dispara este task.
- Busca Attempts cerrados en las últimas `WEBFLEET_SYNC_LOOKBACK_H` horas
  (default 24) cuyo `webfleetSyncedAt` está a NULL.
- Para cada uno llama a `sync_attempt_gps(source='periodic')`.
- Errores individuales se logean pero no abortan el batch.

Si Webfleet está caído, el circuit breaker corta. Próxima ejecución reintentará.
"""
from datetime import datetime, timedelta

from celery import shared_task
from flask import current_app
from loguru import logger

from app.models.session import Attempt, AttemptStatus
from app.services.webfleet import sync_attempt_gps, WebfleetSyncError


@shared_task(name="training.webfleet_sync_recent")
def webfleet_sync_recent():
    """Sincroniza Attempts cerrados recientes que aún no tienen GPS de Webfleet."""
    lookback_h = int(current_app.config.get("WEBFLEET_SYNC_LOOKBACK_H", 24))
    cutoff = datetime.utcnow() - timedelta(hours=lookback_h)

    pending = (
        Attempt.query
        .filter(Attempt.status == AttemptStatus.CLOSED)
        .filter(Attempt.closedAt >= cutoff)
        .filter(Attempt.webfleetSyncedAt.is_(None))
        .all()
    )

    if not pending:
        logger.info("Webfleet sync: ningún attempt pendiente en últimas %sh", lookback_h)
        return {"synced": 0, "errors": 0}

    synced = 0
    errors = 0
    for attempt in pending:
        try:
            sync_attempt_gps(attempt.id, actor_id=None, source="periodic")
            synced += 1
        except WebfleetSyncError as exc:
            logger.warning("Webfleet sync error attempt=%s: %s", attempt.id, exc)
            errors += 1

    logger.info("Webfleet sync done: %s synced, %s errors", synced, errors)
    return {"synced": synced, "errors": errors}
