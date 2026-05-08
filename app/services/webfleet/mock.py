"""Datos sintéticos para correr el flujo Webfleet sin credenciales reales.

Genera puntos GPS plausibles dentro del bounding box de Madrid simulando un
recorrido alrededor de la base de bomberos, con velocidades realistas. El
output respeta el formato de `show_tracks` para que el normalizer trate los
datos igual que los reales.

Uso interno: `client.show_tracks` cae en este módulo cuando WEBFLEET_ENABLED
es False o faltan credenciales.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta

# Centroide aproximado base de bomberos de CMadrid (Vallecas) — punto inicial
# del recorrido sintético.
_BASE_LAT = 40.3833
_BASE_LON = -3.6500


def _walk(seed: int, steps: int):
    """Random walk determinista por seed (objectno) para reproducibilidad."""
    lat = _BASE_LAT
    lon = _BASE_LON
    speed_kmh = 0.0
    for i in range(steps):
        # Movimiento pseudo-aleatorio derivado del seed e índice.
        angle = (seed * 31 + i * 7) % 360
        delta = 0.0002 * (1 + (i % 5))
        lat += delta * math.cos(math.radians(angle))
        lon += delta * math.sin(math.radians(angle))
        # Speed entre 0 y 80 km/h con perfil tipo conducción urbana.
        speed_kmh = 20 + 30 * abs(math.sin((seed + i) / 3.0))
        yield lat, lon, speed_kmh


def show_tracks(object_no: str, range_from: datetime, range_to: datetime) -> list[dict]:
    """
    Genera ~1 punto/segundo entre range_from y range_to (cap 600 puntos).

    El formato imita la respuesta JSON de Webfleet.connect show_tracks:
        pos_time   ISO timestamp
        latitude   grados WGS84 (1e-6 internamente, normalizer lo maneja)
        longitude  grados WGS84
        speed      km/h
        course     dirección 0-359
    """
    duration_s = max(0, int((range_to - range_from).total_seconds()))
    steps = min(duration_s, 600)  # cap razonable
    if steps == 0:
        return []

    seed = sum(ord(c) for c in (object_no or "MOCK"))
    walker = _walk(seed, steps)
    rows: list[dict] = []
    for i, (lat, lon, speed_kmh) in enumerate(walker):
        ts = range_from + timedelta(seconds=i)
        rows.append({
            "pos_time": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "speed": round(speed_kmh, 1),
            "course": (seed + i * 11) % 360,
            "objectno": object_no,
            "_mock": True,
        })
    return rows
