"""Worker periódico que sincroniza GPS y rotativo de Attempts desde Webfleet.

Lógica:
- Cada `WEBFLEET_SYNC_INTERVAL_MIN` (default 10) Celery dispara este task.
- Busca Attempts OPEN en las últimas `WEBFLEET_SYNC_LOOKBACK_H` horas que ya
  tienen datos de estabilidad pero no GPS de Webfleet.
- Para cada uno llama a `sync_attempt_gps` + `sync_attempt_rotativo`.
- Si después del sync los tres tipos de datos están presentes, llama a
  `check_and_autoclose` que dispara el pipeline y cierra el Attempt.
- Errores individuales se logean pero no abortan el batch.

Si Webfleet está caído, el circuit breaker corta. Próxima ejecución reintentará.
"""
from datetime import datetime, timedelta

from celery import shared_task
from flask import current_app
from loguru import logger
from sqlalchemy import exists

from app.models.session import Attempt, AttemptStatus, StabilityMeasurement, GpsMeasurement
from app.services.webfleet import (
    sync_attempt_gps,
    sync_attempt_rotativo,
    check_and_autoclose,
    WebfleetSyncError,
)


@shared_task(name="training.webfleet_sync_recent")
def webfleet_sync_recent():
    """
    Sincroniza GPS + rotativo de Attempts OPEN que ya tienen datos de estabilidad.
    Si los tres tipos de datos quedan completos, cierra automáticamente el Attempt.
    """
    lookback_h = int(current_app.config.get("WEBFLEET_SYNC_LOOKBACK_H", 24))
    cutoff = datetime.utcnow() - timedelta(hours=lookback_h)

    # Attempts OPEN en la ventana de lookback que tienen estabilidad pero NO GPS de Webfleet.
    has_stability = exists().where(StabilityMeasurement.attemptId == Attempt.id)
    has_gps_wf = exists().where(
        (GpsMeasurement.attemptId == Attempt.id) &
        (GpsMeasurement.quality == "WEBFLEET")
    )

    pending = (
        Attempt.query
        .filter(Attempt.status == AttemptStatus.OPEN)
        .filter(Attempt.startTime >= cutoff)
        .filter(has_stability)
        .filter(~has_gps_wf)
        .all()
    )

    if not pending:
        logger.info("Webfleet sync: ningún attempt pendiente en últimas %sh", lookback_h)
        return {"synced_gps": 0, "synced_rot": 0, "autoclosed": 0, "errors": 0}

    synced_gps = 0
    synced_rot = 0
    autoclosed = 0
    errors = 0

    for attempt in pending:
        # Sync GPS
        try:
            sync_attempt_gps(attempt.id, actor_id=None, source="periodic")
            synced_gps += 1
        except WebfleetSyncError as exc:
            logger.warning("Webfleet GPS sync error attempt=%s: %s", attempt.id, exc)
            errors += 1

        # Sync rotativo
        try:
            sync_attempt_rotativo(attempt.id, actor_id=None, source="periodic")
            synced_rot += 1
        except WebfleetSyncError as exc:
            logger.warning("Webfleet rotativo sync error attempt=%s: %s", attempt.id, exc)

        # Auto-close si todos los datos están
        try:
            closed = check_and_autoclose(attempt.id)
            if closed:
                autoclosed += 1
                logger.info("Auto-close attempt=%s tras sync periódico", attempt.id)
        except Exception as exc:
            logger.error("Auto-close error attempt=%s: %s", attempt.id, exc)

    logger.info(
        "Webfleet sync done: gps=%s rot=%s closed=%s errors=%s",
        synced_gps, synced_rot, autoclosed, errors,
    )
    return {
        "synced_gps": synced_gps,
        "synced_rot": synced_rot,
        "autoclosed": autoclosed,
        "errors": errors,
    }
