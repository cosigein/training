"""
Orquesta el pipeline completo de scoring para un Attempt:
    detect_events → calculate_score → cierre del attempt

Idempotente dentro de un mismo attempt: se puede re-ejecutar si no está cerrado.
Si el attempt YA está cerrado, lanza ValueError.
"""
from datetime import datetime

from app.extensions import db
from app.models.session import Attempt, AttemptStatus
from app.models.training import TrainingAuditLog, AuditAction
from .event_detector import detect_events
from .scorer import calculate_score


def run_pipeline(attempt_id, actor_id=None):
    """
    Ejecuta detect → score → cierre para el attempt.

    Args:
        attempt_id: ID del Attempt a procesar.
        actor_id:   ID del User que dispara el pipeline (para audit log).

    Returns:
        dict con: attempt_id, events_detected, score, scoreRaw, breakdown.
    Raises:
        ValueError si el attempt no existe o ya está cerrado.
    """
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        raise ValueError(f"Attempt {attempt_id} no encontrado")
    if attempt.closedAt:
        raise ValueError("Attempt ya cerrado — no se puede re-procesar")

    # Marcar en proceso para evitar ejecuciones paralelas
    attempt.status = AttemptStatus.PROCESSING
    db.session.commit()

    try:
        events_n = detect_events(attempt_id)
        result = calculate_score(attempt_id)

        # Refrescar después de los commits de detect/score
        attempt = Attempt.query.get(attempt_id)
        attempt.status = AttemptStatus.CLOSED
        attempt.closedAt = datetime.utcnow()
        if not attempt.endTime:
            attempt.endTime = attempt.closedAt

        db.session.add(TrainingAuditLog(
            actorId=actor_id,
            actorRole="ADMIN",
            action=AuditAction.SCORE_CALCULATED,
            resourceType="Attempt",
            resourceId=attempt_id,
            delta={"score": result["score"], "events_detected": events_n},
            organizationId=attempt.organizationId,
        ))

        db.session.commit()

    except Exception:
        # Revertir a OPEN para que se pueda reintentar
        attempt = Attempt.query.get(attempt_id)
        if attempt and attempt.status == AttemptStatus.PROCESSING:
            attempt.status = AttemptStatus.OPEN
            db.session.commit()
        raise

    return {
        "attempt_id": attempt_id,
        "events_detected": events_n,
        **result,
    }
