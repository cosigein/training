"""
Scheduler en proceso (APScheduler) para las tareas periódicas del dominio Training.

Se inicia automáticamente con la app Flask — no requiere proceso separado.
Los jobs son exactamente la misma lógica que los Celery tasks de ranking_worker.py,
pero ejecutados en un hilo background dentro del proceso del servidor.

Jobs:
  compute_daily_rankings     06:00 Europe/Madrid — snapshot provisional del ranking
  lock_closed_convocatorias  cada 15 min        — CLOSED → LOCKED
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

_scheduler = BackgroundScheduler(timezone="Europe/Madrid")


def _run_compute_daily_rankings(app):
    with app.app_context():
        from app.workers.ranking_worker import _build_snapshot
        from app.models.training import Convocatoria, ConvocatoriaStatus, RankingStatus
        from app.extensions import db

        convs = Convocatoria.query.filter_by(status=ConvocatoriaStatus.OPEN).all()
        logger.info("scheduler: compute_daily_rankings — {} convocatorias OPEN", len(convs))
        total = 0
        for conv in convs:
            try:
                n = _build_snapshot(conv, RankingStatus.PROVISIONAL)
                logger.info("scheduler: ranking conv={} → {} entradas", conv.id, n)
                total += n
            except Exception as exc:
                logger.error("scheduler: ranking conv={} falló: {}", conv.id, exc)
                db.session.rollback()
        logger.info("scheduler: compute_daily_rankings finalizado — {} entradas", total)


def _run_lock_closed_convocatorias(app):
    with app.app_context():
        from datetime import datetime
        from app.models.training import Convocatoria, ConvocatoriaStatus
        from app.extensions import db

        now = datetime.utcnow()
        try:
            updated = (
                db.session.query(Convocatoria)
                .filter(
                    Convocatoria.status == ConvocatoriaStatus.CLOSED,
                    Convocatoria.reverseWindowUntil < now,
                )
                .update({"status": ConvocatoriaStatus.LOCKED}, synchronize_session=False)
            )
            db.session.commit()
            if updated:
                logger.info("scheduler: {} convocatorias → LOCKED", updated)
        except Exception as exc:
            db.session.rollback()
            logger.error("scheduler: lock_closed_convocatorias falló: {}", exc)


def init_scheduler(app):
    """Registra los jobs y arranca el scheduler. Llamar desde create_app()."""
    if _scheduler.running:
        return

    _scheduler.add_job(
        func=_run_compute_daily_rankings,
        args=[app],
        trigger=CronTrigger(hour=6, minute=0, timezone="Europe/Madrid"),
        id="compute_daily_rankings",
        name="Ranking diario 06:00 Madrid",
        replace_existing=True,
    )

    _scheduler.add_job(
        func=_run_lock_closed_convocatorias,
        args=[app],
        trigger=CronTrigger(minute="*/15"),
        id="lock_closed_convocatorias",
        name="CLOSED→LOCKED cada 15 min",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(
        "scheduler iniciado: {} jobs registrados",
        len(_scheduler.get_jobs()),
    )
