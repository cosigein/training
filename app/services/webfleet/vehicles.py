"""Sincronización de vehículos desde Webfleet.connect (showObjectReport).

Lógica:
- Llama a showObjectReport para obtener todos los vehículos de la cuenta.
- Para cada vehículo recibido:
    * Si existe en la BD por webfleetObjectNo → actualiza webfleetData,
      webfleetLastSeen, webfleetVisible=True y campos básicos.
    * Si NO existe → crea un Vehicle nuevo con los datos de Webfleet.
- Vehículos en la BD con webfleetObjectNo que NO aparecieron en la respuesta
  → webfleetVisible=False (se muestran grises en la UI, no se borran).

La llamada es por organización: si una org tiene al menos un vehículo con
webfleetObjectNo mapeado, sincronizamos su flota completa desde Webfleet.
"""
from datetime import datetime
from typing import Optional

from loguru import logger

from app.extensions import db
from app.models.vehicle import Vehicle, VehicleType, VehicleStatus
from .client import show_object_report, WebfleetError


def _decode_coord(val) -> Optional[float]:
    """Webfleet puede devolver lat/lon como int×1e-6 o float directo."""
    if val is None:
        return None
    try:
        f = float(val)
        # Si el valor absoluto supera 180, asumimos que está en unidades 1e-6.
        return f / 1_000_000 if abs(f) > 180 else f
    except (ValueError, TypeError):
        return None


def _parse_ts(val) -> Optional[datetime]:
    if not val:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(str(val).strip(), fmt)
        except ValueError:
            continue
    return None


def sync_vehicles_from_webfleet(org_id: str) -> dict:
    """
    Sincroniza la flota de la organización con Webfleet.

    Returns:
        {updated, created, disappeared, errors}
    """
    try:
        raw = show_object_report()
    except WebfleetError as exc:
        logger.error("sync_vehicles_from_webfleet: Webfleet error — %s", exc)
        return {"updated": 0, "created": 0, "disappeared": 0, "errors": 1}

    now = datetime.utcnow()

    # Index de vehículos recibidos por objectno
    by_objectno: dict[str, dict] = {}
    for row in raw:
        ono = row.get("objectno")
        if ono:
            by_objectno[ono] = row

    # Vehículos de la org que tienen webfleetObjectNo
    db_vehicles = Vehicle.query.filter_by(organizationId=org_id).filter(
        Vehicle.webfleetObjectNo.isnot(None)
    ).all()
    db_by_ono = {v.webfleetObjectNo: v for v in db_vehicles}

    updated = 0
    created = 0
    disappeared = 0

    # ── Actualizar / crear ─────────────────────────────────────────────────────
    for ono, row in by_objectno.items():
        vehicle = db_by_ono.get(ono)

        if vehicle:
            # Actualizar campos básicos + snapshot
            vehicle.name = row.get("objectname") or vehicle.name
            vehicle.webfleetData = row
            vehicle.webfleetLastSeen = now
            vehicle.webfleetVisible = True
            updated += 1
        else:
            # Vehículo nuevo descubierto en Webfleet — registrar con datos mínimos.
            # La matrícula real la pondrá el manager; usamos el objectno como placeholder.
            plate_placeholder = f"WF-{ono}"[:20]
            if Vehicle.query.filter_by(licensePlate=plate_placeholder).first():
                plate_placeholder = f"WF-{ono[:16]}-{created}"

            new_v = Vehicle(
                organizationId=org_id,
                name=row.get("objectname") or ono,
                model=row.get("objectclassname") or "Webfleet",
                licensePlate=plate_placeholder,
                identifier=ono,
                type=VehicleType.FIRE_TRUCK,
                status=VehicleStatus.ACTIVE,
                webfleetObjectNo=ono,
                webfleetData=row,
                webfleetLastSeen=now,
                webfleetVisible=True,
            )
            db.session.add(new_v)
            created += 1
            logger.info("Nuevo vehículo descubierto en Webfleet: %s (%s)", ono, row.get("objectname"))

    # ── Marcar desaparecidos ───────────────────────────────────────────────────
    for ono, vehicle in db_by_ono.items():
        if ono not in by_objectno:
            vehicle.webfleetVisible = False
            disappeared += 1
            logger.warning("Vehículo %s desapareció de Webfleet — marcado invisible", ono)

    db.session.commit()

    logger.info(
        "sync_vehicles org=%s updated=%s created=%s disappeared=%s",
        org_id, updated, created, disappeared,
    )
    return {"updated": updated, "created": created, "disappeared": disappeared, "errors": 0}
