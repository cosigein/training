"""
Workers Celery — dominio Training (T9).

Tasks:
  compute_daily_rankings    06:00 Europe/Madrid — snapshot provisional del ranking
                            de cada convocatoria OPEN. Insert-only sobre Ranking.

  lock_closed_convocatorias cada 15 min — transición CLOSED→LOCKED una vez que
                            expira la ventana de reversa de 24 h.

Usar @shared_task para no atar las definiciones a una instancia Celery concreta;
celery_worker.py se encarga de vincular al crear la app.
"""
from datetime import datetime

from celery import shared_task
from loguru import logger

from app.extensions import db
from app.models.training import (
    Convocatoria, ConvocatoriaStatus,
    Enrollment, EnrollmentStatus,
    Ranking, RankingStatus,
    TrainingAuditLog, AuditAction,
)
from app.models.session import Attempt, AttemptStatus


# ── helpers ───────────────────────────────────────────────────────────────────

def _nota_media(enrollment_id):
    """Media de scores de attempts CLOSED con score no nulo."""
    rows = (
        Attempt.query
        .filter_by(enrollmentId=enrollment_id, status=AttemptStatus.CLOSED)
        .filter(Attempt.score.isnot(None))
        .with_entities(Attempt.score)
        .all()
    )
    scores = [r.score for r in rows]
    return sum(scores) / len(scores) if scores else 0.0


def _stability_media(enrollment_id):
    """Media de stability_family_score (scoreBreakdown['estabilidad']) de attempts CLOSED."""
    rows = (
        Attempt.query
        .filter_by(enrollmentId=enrollment_id, status=AttemptStatus.CLOSED)
        .filter(Attempt.score.isnot(None))
        .with_entities(Attempt.scoreBreakdown)
        .all()
    )
    vals = []
    for r in rows:
        bd = r.scoreBreakdown
        if isinstance(bd, dict) and "estabilidad" in bd:
            vals.append(bd["estabilidad"])
    return sum(vals) / len(vals) if vals else 0.0


def _low_data_quality_rate(enrollment_id):
    """Proporción de attempts CLOSED con dataQuality confidence < 0.5 ('LOW')."""
    rows = (
        Attempt.query
        .filter_by(enrollmentId=enrollment_id, status=AttemptStatus.CLOSED)
        .filter(Attempt.score.isnot(None))
        .with_entities(Attempt.dataQuality)
        .all()
    )
    if not rows:
        return 0.0
    low_count = 0
    for r in rows:
        dq = r.dataQuality
        if isinstance(dq, dict):
            low_count += 1 if dq.get("confidenceScore", 1.0) < 0.5 else 0
    return low_count / len(rows)


def _sort_key(entry):
    """
    Cascada de desempate (D19):
    1° nota_media desc
    2° tasa_low_quality asc (menor tasa de datos malos)
    3° stability_media desc
    4° enrolled_at asc (primero en inscribirse gana el sorteo determinista V1)
    """
    return (
        -entry["nota_media"],
        entry["low_dq_rate"],
        -entry["stability_media"],
        entry["enrolled_at"].timestamp() if entry["enrolled_at"] else 0,
    )


def _build_snapshot(conv, status):
    """Calcula el ranking provisional o definitivo de una convocatoria y persiste filas."""
    enrollments = (
        Enrollment.query
        .filter_by(convocatoriaId=conv.id, organizationId=conv.organizationId)
        .filter(Enrollment.status == EnrollmentStatus.ACTIVE)
        .all()
    )
    if not enrollments:
        logger.info("ranking: convocatoria {} sin enrollments activos, skip", conv.id)
        return 0

    entries = []
    for e in enrollments:
        nota = _nota_media(e.id)
        scored_count = (
            Attempt.query
            .filter_by(enrollmentId=e.id, status=AttemptStatus.CLOSED)
            .filter(Attempt.score.isnot(None))
            .count()
        )
        entries.append({
            "enrollment": e,
            "nota_media": nota,
            "rutas_completadas": scored_count,
            "low_dq_rate": _low_data_quality_rate(e.id),
            "stability_media": _stability_media(e.id),
            "enrolled_at": e.enrolledAt,
        })

    entries.sort(key=_sort_key)

    snapshot_at = datetime.utcnow()
    for puesto, entry in enumerate(entries, start=1):
        e = entry["enrollment"]
        db.session.add(Ranking(
            convocatoriaId=conv.id,
            enrollmentId=e.id,
            studentId=e.studentId,
            score=round(entry["nota_media"], 2),
            rank=puesto,
            status=status,
            snapshotAt=snapshot_at,
        ))

    db.session.add(TrainingAuditLog(
        actorId=None,
        actorRole="SYSTEM",
        action=AuditAction.RANKING_PUBLISHED,
        resourceType="Convocatoria",
        resourceId=conv.id,
        delta={
            "status": status.value,
            "entries": len(entries),
            "snapshotAt": snapshot_at.isoformat(),
        },
        organizationId=conv.organizationId,
    ))
    db.session.commit()
    return len(entries)


# ── tasks ─────────────────────────────────────────────────────────────────────

@shared_task(name="training.compute_daily_rankings", bind=True, max_retries=3)
def compute_daily_rankings(self):
    """
    Calcula y persiste un snapshot PROVISIONAL del ranking para cada
    convocatoria OPEN. Se ejecuta diariamente a las 06:00 Europe/Madrid.
    """
    convs = (
        Convocatoria.query
        .filter_by(status=ConvocatoriaStatus.OPEN)
        .all()
    )
    logger.info("ranking cron: {} convocatorias OPEN", len(convs))

    total = 0
    for conv in convs:
        try:
            n = _build_snapshot(conv, RankingStatus.PROVISIONAL)
            logger.info("ranking: conv={} → {} entradas", conv.id, n)
            total += n
        except Exception as exc:
            logger.error("ranking: conv={} falló: {}", conv.id, exc)
            db.session.rollback()
            # Reintenta el task completo si es la primera falla
            raise self.retry(exc=exc, countdown=300)

    logger.info("ranking cron finalizado: {} entradas totales", total)
    return {"convocatorias": len(convs), "entries": total}


@shared_task(name="training.lock_closed_convocatorias", bind=True, max_retries=3)
def lock_closed_convocatorias(self):
    """
    Transiciona CLOSED → LOCKED para convocatorias cuya ventana de reversa
    de 24 h ya expiró. Se ejecuta cada 15 min.
    """
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
    except Exception as exc:
        db.session.rollback()
        logger.error("lock_closed_convocatorias falló: {}", exc)
        raise self.retry(exc=exc, countdown=60)

    if updated:
        logger.info("lock_closed: {} convocatorias → LOCKED", updated)
    return {"locked": updated}
