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
# Inestabilidad combinada: |accmag - gravedad| por encima = maniobra brusca
# en cualquier eje (capta combinaciones lat+long que aisladas no cruzan umbral).
_ACCMAG_DELTA_THRESHOLD = 2.5
_GRAVITY = 9.81            # m/s² nominal de la gravedad

# Velocidad máxima permitida (km/h) — sin límite de ruta específico
_DEFAULT_SPEED_LIMIT_KMH = 90.0

# Persistencia mínima: muestras consecutivas (gap ≤ MAX_GAP_MS) sobre el umbral
# antes de aceptar un evento como real (filtra picos espurios del sensor).
_MIN_PERSISTENCE = 2
# Dos muestras de StabilityMeasurement están a ~100 ms; tolerar hasta 200 ms.
_MAX_GAP_MS = 200

# Debounce entre eventos consecutivos del mismo tipo (segundos): luego de
# emitir uno, ignorar otros nuevos del mismo tipo dentro de esta ventana.
_DEBOUNCE_S = 1

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


_SEV_RANK = {
    EventSeverity.LOW: 0,
    EventSeverity.MEDIUM: 1,
    EventSeverity.HIGH: 2,
    EventSeverity.CRITICAL: 3,
}


def _filter_runs(events):
    """
    Filtra y agrupa los eventos crudos en eventos finales:

    1. Agrupa por tipo.
    2. Detecta "runs" (corridas) de muestras consecutivas del mismo tipo cuyo
       gap entre muestras es ≤ _MAX_GAP_MS — eso significa "una misma maniobra".
    3. Solo emite runs con tamaño ≥ _MIN_PERSISTENCE (descarta picos aislados
       que son ruido del sensor).
    4. Para cada run válido emite UN evento con la severidad más alta del run
       y timestamp del peak.
    5. Aplica debounce de _DEBOUNCE_S entre eventos del mismo tipo (evita que
       dos runs separados por menos de 1 s se cuenten como dos eventos cuando
       son la misma maniobra continuada).
    """
    if not events:
        return []

    by_type = {}
    for ev in events:
        by_type.setdefault(ev["type"], []).append(ev)

    result = []
    for _, evs in by_type.items():
        evs_sorted = sorted(evs, key=lambda e: e["timestamp"])

        # Formar clusters por proximidad temporal
        clusters = []
        current = [evs_sorted[0]]
        for ev in evs_sorted[1:]:
            gap_ms = (ev["timestamp"] - current[-1]["timestamp"]).total_seconds() * 1000.0
            if gap_ms <= _MAX_GAP_MS:
                current.append(ev)
            else:
                clusters.append(current)
                current = [ev]
        clusters.append(current)

        # Emitir un evento por cluster válido, aplicando debounce
        last_emit_ts = None
        for cluster in clusters:
            if len(cluster) < _MIN_PERSISTENCE:
                continue
            peak = max(cluster, key=lambda e: _SEV_RANK[e["severity"]])
            if last_emit_ts is not None:
                if (peak["timestamp"] - last_emit_ts).total_seconds() < _DEBOUNCE_S:
                    continue
            last_emit_ts = peak["timestamp"]
            result.append(peak)

    return sorted(result, key=lambda e: e["timestamp"])


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

        # Inestabilidad combinada: el módulo de aceleración total se aparta
        # significativamente de la gravedad → maniobra brusca en cualquier eje.
        if s.accmag is not None:
            delta_g = abs(s.accmag - _GRAVITY)
            if delta_g > _ACCMAG_DELTA_THRESHOLD:
                sev = _sev_from_lateral(delta_g)
                raw_events.append({
                    "type": AttemptEventType.ACCELERATION_LATERAL,
                    "severity": sev,
                    "source": EventSource.DOBACK_ELITE,
                    "confidence": conf,
                    "timestamp": s.timestamp,
                    "penaltyPoints": _PENALTY[sev],
                    "payload": {"accmag": round(s.accmag, 3), "delta_g": round(delta_g, 3)},
                })

        if any([s.isDRSHigh, s.isLTRCritical, s.isLateralGForceHigh]):
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

    # ── Persistencia + clustering + debounce ────────────────────────────────
    filtered = _filter_runs(raw_events)

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
