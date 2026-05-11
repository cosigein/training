"""Servicio de sincronización Webfleet → GpsMeasurement.

`sync_attempt_gps(attempt_id, source)` orquesta el flujo:
    1. Carga el Attempt y su Vehicle.
    2. Resuelve `vehicle.webfleetObjectNo` (error si falta).
    3. Pide a Webfleet `show_tracks` por el rango temporal del attempt.
    4. Normaliza la respuesta.
    5. Borra GpsMeasurement previos del attempt e inserta los nuevos
       (idempotente: re-syncs sobreescriben).
    6. Marca `attempt.webfleetSyncedAt` y `webfleetSyncSource`.
    7. Audit log.
"""
from datetime import datetime, timedelta
from typing import Optional

from loguru import logger

from app.extensions import db
from app.models.session import Attempt, GpsMeasurement, StabilityMeasurement, RotativoMeasurement
from app.models.training import TrainingAuditLog, AuditAction
from app.models.vehicle import Vehicle

from .client import show_tracks, show_digital_events, WebfleetError
from .normalizer import normalize_show_tracks


def get_attempt_data_status(attempt_id: str) -> dict:
    """
    Comprueba qué fuentes de datos tiene el Attempt.

    Returns:
        {
          has_stability: bool,  # datos del Doback Elite subidos por el manager
          has_gps:       bool,  # GPS sincronizado desde Webfleet
          has_rotativo:  bool,  # rotativo sincronizado desde Webfleet
          is_complete:   bool,  # los tres presentes → listo para pipeline
        }
    """
    has_stability = StabilityMeasurement.query.filter_by(attemptId=attempt_id).first() is not None
    has_gps = GpsMeasurement.query.filter_by(attemptId=attempt_id, quality="WEBFLEET").first() is not None
    has_rotativo = RotativoMeasurement.query.filter_by(attemptId=attempt_id).first() is not None
    return {
        "has_stability": has_stability,
        "has_gps": has_gps,
        "has_rotativo": has_rotativo,
        "is_complete": has_stability and has_gps and has_rotativo,
    }


def check_and_autoclose(attempt_id: str, actor_id: Optional[str] = None) -> bool:
    """
    Si el Attempt tiene los tres tipos de datos, dispara el pipeline y lo cierra.

    Returns:
        True si se cerró en esta llamada, False si falta algún dato o ya estaba cerrado.
    """
    attempt = Attempt.query.get(attempt_id)
    if not attempt or attempt.closedAt:
        return False

    status = get_attempt_data_status(attempt_id)
    if not status["is_complete"]:
        return False

    from app.services.pipeline.pipeline import run_pipeline
    run_pipeline(attempt_id, actor_id=actor_id)
    logger.info("Auto-close attempt=%s (todos los datos presentes)", attempt_id)
    return True


class WebfleetSyncError(Exception):
    pass


def sync_attempt_gps(
    attempt_id: str,
    actor_id: Optional[str] = None,
    source: str = "manual",
) -> dict:
    """
    Sincroniza los GpsMeasurement del attempt desde Webfleet.

    Args:
        attempt_id: ID del Attempt a sincronizar.
        actor_id:   ID del User que dispara (None si es worker periódico).
        source:     'manual' | 'periodic' | 'mock'. Se persiste en
                    Attempt.webfleetSyncSource para trazabilidad.

    Returns:
        dict con: rows_inserted, range_from, range_to, was_mock.

    Raises:
        WebfleetSyncError: cualquier problema (vehicle sin objectno,
                           attempt sin rango, error de Webfleet, etc.).
    """
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        raise WebfleetSyncError(f"Attempt {attempt_id} no encontrado")

    if not attempt.startTime:
        raise WebfleetSyncError("El Attempt no tiene startTime — no se puede acotar el rango")

    vehicle = Vehicle.query.get(attempt.vehicleId) if attempt.vehicleId else None
    if not vehicle:
        raise WebfleetSyncError("El Attempt no tiene Vehicle asociado")
    if not vehicle.webfleetObjectNo:
        raise WebfleetSyncError(
            f"El vehículo {vehicle.name} no tiene mapeado un objectno de Webfleet. "
            "Configurá `Vehicle.webfleetObjectNo` antes de sincronizar."
        )

    # Rango: desde startTime hasta endTime (o ahora + buffer si está abierto).
    range_from = attempt.startTime
    range_to = attempt.endTime or (datetime.utcnow() + timedelta(minutes=5))
    # Pequeño buffer al rango para absorber clock skew Doback ↔ Webfleet.
    range_from = range_from - timedelta(seconds=30)
    range_to = range_to + timedelta(seconds=30)

    try:
        raw_rows = show_tracks(vehicle.webfleetObjectNo, range_from, range_to)
    except WebfleetError as exc:
        raise WebfleetSyncError(str(exc)) from exc

    rows = normalize_show_tracks(raw_rows)
    was_mock = bool(raw_rows and raw_rows[0].get("_mock"))

    # Idempotente: borrar mediciones previas de Webfleet y reinsertar.
    # NO tocamos las del Doback Elite — esas se borran solo en el flujo
    # del parser. Distinción por `quality`:
    GpsMeasurement.query.filter_by(
        attemptId=attempt_id, quality="WEBFLEET"
    ).delete()

    for r in rows:
        db.session.add(GpsMeasurement(
            attemptId=attempt_id,
            organizationId=attempt.organizationId,
            timestamp=r["timestamp"],
            latitude=r["latitude"],
            longitude=r["longitude"],
            altitude=r["altitude"],
            speed=r["speed"],
            satellites=r.get("satellites"),
            hdop=r.get("hdop"),
            fix=r.get("fix"),
            heading=r.get("heading"),
            quality="WEBFLEET",
            confidence=0.9 if not was_mock else 0.5,
        ))

    attempt.webfleetSyncedAt = datetime.utcnow()
    attempt.webfleetSyncSource = "mock" if was_mock else source

    db.session.add(TrainingAuditLog(
        actorId=actor_id,
        actorRole="MANAGER" if source == "manual" else "SYSTEM",
        action=AuditAction.SCORE_CALCULATED,  # reusa enum existente; ver nota *
        resourceType="Attempt",
        resourceId=attempt_id,
        delta={
            "webfleet_sync": True,
            "rows_inserted": len(rows),
            "range_from": range_from.isoformat(),
            "range_to": range_to.isoformat(),
            "source": "mock" if was_mock else source,
        },
        organizationId=attempt.organizationId,
    ))

    db.session.commit()

    logger.info(
        "Webfleet sync attempt=%s rows=%s mock=%s source=%s",
        attempt_id, len(rows), was_mock, source,
    )

    return {
        "attempt_id": attempt_id,
        "rows_inserted": len(rows),
        "range_from": range_from,
        "range_to": range_to,
        "was_mock": was_mock,
    }


def sync_attempt_rotativo(
    attempt_id: str,
    actor_id: Optional[str] = None,
    source: str = "manual",
) -> dict:
    """
    Sincroniza los RotativoMeasurement del attempt desde Webfleet (showIOReportExtern).

    showIOReportExtern requiere el permiso "Digital I/O report" en el API key.
    Si no está disponible, el cliente hace fallback a mock automáticamente.

    Mismo contrato que `sync_attempt_gps`: idempotente, usa circuit breaker y
    rate limiter, funciona en modo mock sin credenciales.
    """
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        raise WebfleetSyncError(f"Attempt {attempt_id} no encontrado")

    if not attempt.startTime:
        raise WebfleetSyncError("El Attempt no tiene startTime — no se puede acotar el rango")

    vehicle = Vehicle.query.get(attempt.vehicleId) if attempt.vehicleId else None
    if not vehicle:
        raise WebfleetSyncError("El Attempt no tiene Vehicle asociado")
    if not vehicle.webfleetObjectNo:
        raise WebfleetSyncError(
            f"El vehículo {vehicle.name} no tiene mapeado un objectno de Webfleet. "
            "Configurá `Vehicle.webfleetObjectNo` antes de sincronizar."
        )

    range_from = attempt.startTime - timedelta(seconds=30)
    range_to = attempt.endTime or (datetime.utcnow() + timedelta(minutes=5))
    range_to = range_to + timedelta(seconds=30)

    try:
        raw_rows = show_digital_events(vehicle.webfleetObjectNo, range_from, range_to)
    except WebfleetError as exc:
        raise WebfleetSyncError(str(exc)) from exc

    was_mock = bool(raw_rows and raw_rows[0].get("_mock"))

    RotativoMeasurement.query.filter_by(attemptId=attempt_id).delete()

    inserted = 0
    for r in raw_rows:
        # showIOReportExtern usa pos_time; mock y showIOActivities usan msg_time.
        raw_ts = r.get("pos_time") or r.get("msg_time") or r.get("recvtime", "")
        ts = None
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                ts = datetime.strptime(raw_ts.strip(), fmt)
                break
            except (ValueError, AttributeError):
                continue
        if ts is None:
            continue

        # showIOReportExtern expone las entradas como io_1, io_2... o input_value.
        # Canal 1 = rotativo por convención de CMadrid.
        input_val = str(
            r.get("io_1")
            or r.get("input_1")
            or r.get("input_value")
            or "0"
        )
        state = "1" if input_val.strip() in ("1", "true", "on", "ON", "active") else "0"
        db.session.add(RotativoMeasurement(
            attemptId=attempt_id,
            organizationId=attempt.organizationId,
            timestamp=ts,
            state=state,
            key=1,
        ))
        inserted += 1

    db.session.commit()

    logger.info(
        "Webfleet rotativo sync attempt=%s rows=%s mock=%s source=%s",
        attempt_id, inserted, was_mock, source,
    )

    return {
        "attempt_id": attempt_id,
        "rows_inserted": inserted,
        "was_mock": was_mock,
    }


# * Nota: idealmente el enum `AuditAction` tendría `WEBFLEET_SYNCED`. Por
# ahora se reusa SCORE_CALCULATED — el campo `delta.webfleet_sync=True`
# distingue. Cuando agreguemos enum, hacer migración + cambiar acá.
