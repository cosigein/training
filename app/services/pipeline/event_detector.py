"""
Detecta eventos de penalización a partir de las mediciones raw de un Attempt.

Idempotente: re-ejecutar borra los AttemptEvent previos y los recalcula.

Fuentes:
- StabilityMeasurement → HARSH_BRAKING, HARSH_ACCELERATION, ACCELERATION_LATERAL
- CanMeasurement       → HARSH_BRAKING (ABS trigger)
- GpsMeasurement       → SPEEDING

Confianza (confidence 0..1):
- HIGH (≥0.7): señal limpia, GPS con ≥4 satélites y hdop ≤ 2.0
- LOW  (<0.7): baja cobertura GPS, dato interpolado o sensor sin confianza
"""
from app.extensions import db
from app.models.session import Attempt, GpsMeasurement, StabilityMeasurement, CanMeasurement
from app.models.training import (
    AttemptEvent, AttemptEventType, EventSeverity, EventSource,
)

# ── Thresholds (m/s²) ────────────────────────────────────────────────────────
_BRAKE_THRESHOLD = -2.5    # ax por debajo de esto = frenada brusca
_ACCEL_THRESHOLD = 3.0     # ax por encima = aceleración brusca
_LATERAL_THRESHOLD = 2.5   # |ay| por encima = g lateral excesivo

# Velocidad máxima permitida (km/h) — sin límite de ruta específico
_DEFAULT_SPEED_LIMIT_KMH = 90.0

# Debounce: ignorar eventos del mismo tipo dentro de esta ventana (segundos)
_DEBOUNCE_S = 3

# Penalización base por severidad (puntos a restar del score de la familia)
_PENALTY = {
    EventSeverity.LOW: 0.3,
    EventSeverity.MEDIUM: 0.6,
    EventSeverity.HIGH: 1.2,
    EventSeverity.CRITICAL: 2.0,
}


def _sev_from_ax_brake(ax):
    mag = abs(ax)
    if mag >= 8.0:
        return EventSeverity.CRITICAL
    if mag >= 6.0:
        return EventSeverity.HIGH
    if mag >= 4.0:
        return EventSeverity.MEDIUM
    return EventSeverity.LOW


def _sev_from_ax_accel(ax):
    if ax >= 8.0:
        return EventSeverity.CRITICAL
    if ax >= 6.0:
        return EventSeverity.HIGH
    if ax >= 4.0:
        return EventSeverity.MEDIUM
    return EventSeverity.LOW


def _sev_from_lateral(ay):
    mag = abs(ay)
    if mag >= 8.0:
        return EventSeverity.CRITICAL
    if mag >= 6.0:
        return EventSeverity.HIGH
    if mag >= 4.0:
        return EventSeverity.MEDIUM
    return EventSeverity.LOW


def _sev_from_speed_excess(excess_kmh):
    if excess_kmh >= 35:
        return EventSeverity.CRITICAL
    if excess_kmh >= 25:
        return EventSeverity.HIGH
    if excess_kmh >= 15:
        return EventSeverity.MEDIUM
    return EventSeverity.LOW


def _debounce(events):
    """Filtra eventos repetidos dentro de la ventana de debounce por tipo."""
    result = []
    last_ts = {}
    for ev in sorted(events, key=lambda e: e["timestamp"]):
        t = ev["type"]
        ts = ev["timestamp"]
        if t in last_ts and (ts - last_ts[t]).total_seconds() < _DEBOUNCE_S:
            continue
        last_ts[t] = ts
        result.append(ev)
    return result


def detect_events(attempt_id):
    """
    Detecta y persiste AttemptEvent para el attempt dado.

    Returns:
        int — cantidad de eventos insertados.
    Raises:
        ValueError — si el attempt no existe o ya está cerrado.
    """
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        raise ValueError(f"Attempt {attempt_id} no encontrado")
    if attempt.closedAt:
        raise ValueError("Attempt ya cerrado — no se pueden redetectar eventos")

    # Idempotente: borrar eventos previos de este attempt
    AttemptEvent.query.filter_by(attemptId=attempt_id).delete()

    org_id = attempt.organizationId
    raw_events = []

    # ── StabilityMeasurement ─────────────────────────────────────────────────
    for s in (
        StabilityMeasurement.query
        .filter_by(attemptId=attempt_id)
        .order_by(StabilityMeasurement.timestamp)
        .all()
    ):
        conf = s.confidence if s.confidence is not None else 0.7

        if s.ax is not None and s.ax < _BRAKE_THRESHOLD:
            sev = _sev_from_ax_brake(s.ax)
            raw_events.append({
                "type": AttemptEventType.HARSH_BRAKING,
                "severity": sev,
                "source": EventSource.DOBACK_ELITE,
                "confidence": conf,
                "timestamp": s.timestamp,
                "penaltyPoints": _PENALTY[sev],
                "payload": {"ax": round(s.ax, 3), "accmag": s.accmag},
            })

        if s.ax is not None and s.ax > _ACCEL_THRESHOLD:
            sev = _sev_from_ax_accel(s.ax)
            raw_events.append({
                "type": AttemptEventType.HARSH_ACCELERATION,
                "severity": sev,
                "source": EventSource.DOBACK_ELITE,
                "confidence": conf,
                "timestamp": s.timestamp,
                "penaltyPoints": _PENALTY[sev],
                "payload": {"ax": round(s.ax, 3)},
            })

        if s.ay is not None and abs(s.ay) > _LATERAL_THRESHOLD:
            sev = _sev_from_lateral(s.ay)
            raw_events.append({
                "type": AttemptEventType.ACCELERATION_LATERAL,
                "severity": sev,
                "source": EventSource.DOBACK_ELITE,
                "confidence": conf,
                "timestamp": s.timestamp,
                "penaltyPoints": _PENALTY[sev],
                "payload": {"ay": round(s.ay, 3)},
            })
        elif any([s.isDRSHigh, s.isLTRCritical, s.isLateralGForceHigh]):
            sev = EventSeverity.CRITICAL if s.isDRSHigh else EventSeverity.HIGH
            raw_events.append({
                "type": AttemptEventType.ACCELERATION_LATERAL,
                "severity": sev,
                "source": EventSource.DOBACK_ELITE,
                "confidence": conf,
                "timestamp": s.timestamp,
                "penaltyPoints": _PENALTY[sev],
                "payload": {
                    "isDRSHigh": s.isDRSHigh,
                    "isLTRCritical": s.isLTRCritical,
                    "isLateralGForceHigh": s.isLateralGForceHigh,
                },
            })

    # ── CanMeasurement ───────────────────────────────────────────────────────
    for c in (
        CanMeasurement.query
        .filter_by(attemptId=attempt_id)
        .order_by(CanMeasurement.timestamp)
        .all()
    ):
        if c.absActive:
            sev = EventSeverity.HIGH
            raw_events.append({
                "type": AttemptEventType.HARSH_BRAKING,
                "severity": sev,
                "source": EventSource.DOBACK_ELITE,
                "confidence": 0.9,
                "timestamp": c.timestamp,
                "penaltyPoints": _PENALTY[sev],
                "payload": {"absActive": True, "brakePressure": c.brakePressure},
            })

    # ── GpsMeasurement (SPEEDING) ────────────────────────────────────────────
    for g in (
        GpsMeasurement.query
        .filter_by(attemptId=attempt_id)
        .order_by(GpsMeasurement.timestamp)
        .all()
    ):
        if g.speed is None:
            continue
        # GpsMeasurement.speed se almacena en km/h (el parser ya convierte)
        speed_kmh = g.speed
        excess = speed_kmh - _DEFAULT_SPEED_LIMIT_KMH
        if excess <= 5:
            continue
        sev = _sev_from_speed_excess(excess)
        gps_ok = (g.satellites or 0) >= 4 and (g.hdop or 99.0) <= 2.0
        conf = 0.9 if gps_ok else 0.5
        raw_events.append({
            "type": AttemptEventType.SPEEDING,
            "severity": sev,
            "source": EventSource.DOBACK_ELITE,
            "confidence": conf,
            "timestamp": g.timestamp,
            "penaltyPoints": _PENALTY[sev],
            "payload": {
                "speed_kmh": round(speed_kmh, 1),
                "limit_kmh": _DEFAULT_SPEED_LIMIT_KMH,
                "excess_kmh": round(excess, 1),
            },
        })

    # ── Debounce y persistencia ──────────────────────────────────────────────
    filtered = _debounce(raw_events)

    for ev in filtered:
        db.session.add(AttemptEvent(
            attemptId=attempt_id,
            organizationId=org_id,
            type=ev["type"],
            severity=ev["severity"],
            source=ev["source"],
            confidence=ev["confidence"],
            penaltyPoints=ev["penaltyPoints"],
            timestamp=ev["timestamp"],
            payload=ev["payload"],
        ))

    db.session.commit()
    return len(filtered)
