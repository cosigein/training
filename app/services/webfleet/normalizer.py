"""Normalizer: response cruda de Webfleet show_tracks → dicts listos para
GpsMeasurement.

Webfleet.connect históricamente devolvía coordenadas como entero ×1e-6
(p.ej. 40383300 = 40.3833°). En el formato JSON moderno también puede
venir como float decimal. Manejamos ambos.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional


def _to_float(value, default: Optional[float] = None) -> Optional[float]:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _decode_coord(raw) -> Optional[float]:
    """Acepta entero ×1e-6 o float ya en grados. Devuelve grados WGS84."""
    val = _to_float(raw)
    if val is None:
        return None
    # Si la magnitud es típica de coords en 1e-6 (ej. 40383300), normalizar.
    if abs(val) > 1000:
        return val / 1_000_000.0
    return val


def _parse_ts(value) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    s = str(value)
    # Webfleet típicamente devuelve "2026-04-30T10:15:00Z" o
    # "2026-04-30 10:15:00". Probar ambos.
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def normalize_show_tracks(rows: list[dict]) -> list[dict]:
    """
    Convierte la respuesta de show_tracks (lista de dicts crudos) en una
    lista de dicts con las claves que `GpsMeasurement` espera. Filtra filas
    sin coordenadas o sin timestamp.

    Devuelve diccionarios — el caller decide la persistencia.
    """
    out: list[dict] = []
    for row in rows or []:
        ts = _parse_ts(row.get("pos_time") or row.get("timestamp") or row.get("time"))
        lat = _decode_coord(row.get("latitude") or row.get("lat") or row.get("latitude_mdeg"))
        lon = _decode_coord(row.get("longitude") or row.get("lon") or row.get("longitude_mdeg"))

        if ts is None or lat is None or lon is None:
            continue
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            continue

        speed = _to_float(row.get("speed"), 0.0)  # ya en km/h
        heading = _to_float(row.get("course") or row.get("heading"))

        out.append({
            "timestamp": ts,
            "latitude": lat,
            "longitude": lon,
            "altitude": 0.0,
            "speed": speed or 0.0,
            "heading": heading,
            "satellites": None,
            "hdop": None,
            "fix": None,
            "quality": "WEBFLEET",
        })
    return out
