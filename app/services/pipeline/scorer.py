"""
Calcula el score de un Attempt a partir de los AttemptEvent ya persistidos.

Fórmula:
    score_familia = peso_familia * 10 - sum(penaltyPoints de esa familia)
    score_familia = clamp(0, peso_familia * 10)
    score_total   = sum(score_familia)   → 0.0 .. 10.0

Mapeo evento → familia:
    ACCELERATION_LATERAL  → estabilidad
    SPEEDING              → velocidad
    DEVIATION             → ruta  (reservado — no detectado aún)
    HARSH_BRAKING         → conduccion
    HARSH_ACCELERATION    → conduccion

Idempotente: re-ejecutar sobreescribe score/scoreBreakdown/scoreRaw
siempre que el attempt no esté cerrado.
"""
from datetime import datetime

from app.extensions import db
from app.models.session import Attempt, AttemptStatus
from app.models.training import AttemptEvent, AttemptEventType

_DEFAULT_PESOS = {
    "estabilidad": 0.40,
    "velocidad":   0.30,
    "ruta":        0.15,
    "conduccion":  0.15,
}

_FAMILY_MAP = {
    AttemptEventType.ACCELERATION_LATERAL: "estabilidad",
    AttemptEventType.SPEEDING:             "velocidad",
    AttemptEventType.DEVIATION:            "ruta",
    AttemptEventType.HARSH_BRAKING:        "conduccion",
    AttemptEventType.HARSH_ACCELERATION:   "conduccion",
}


def calculate_score(attempt_id):
    """
    Lee los AttemptEvent del attempt, aplica penalizaciones por familia
    y persiste score, scoreRaw y scoreBreakdown en el Attempt.

    Returns:
        dict con keys: score, scoreRaw, breakdown, events_count.
    Raises:
        ValueError — si el attempt no existe o ya está cerrado.
    """
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        raise ValueError(f"Attempt {attempt_id} no encontrado")
    if attempt.closedAt:
        raise ValueError("Attempt ya cerrado — inmutable")

    # Pesos desde la convocatoria o defaults
    pesos = _DEFAULT_PESOS.copy()
    if attempt.convocatoria and attempt.convocatoria.pesosPorFamilia:
        pesos.update(attempt.convocatoria.pesosPorFamilia)

    # Score máximo por familia
    family_scores = {fam: peso * 10.0 for fam, peso in pesos.items()}

    # Aplicar penalizaciones
    events = AttemptEvent.query.filter_by(attemptId=attempt_id).all()
    for ev in events:
        family = _FAMILY_MAP.get(ev.type)
        if family and family in family_scores:
            family_scores[family] = max(0.0, family_scores[family] - (ev.penaltyPoints or 0.0))

    score_raw = sum(family_scores.values())
    score_total = round(min(10.0, max(0.0, score_raw)), 1)
    breakdown = {fam: round(score, 1) for fam, score in family_scores.items()}

    attempt.score = score_total
    attempt.scoreRaw = round(score_raw, 1)
    attempt.scoreBreakdown = breakdown
    attempt.updatedAt = datetime.utcnow()

    db.session.commit()

    return {
        "score": score_total,
        "scoreRaw": round(score_raw, 1),
        "breakdown": breakdown,
        "events_count": len(events),
    }
