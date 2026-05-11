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
import random
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


def show_object_report(object_no: str = None) -> list[dict]:
    """
    Genera un snapshot de estado de vehículos sintético.

    Si object_no está dado, devuelve solo ese vehículo.
    Si no, devuelve todos los vehículos de la BD que tengan webfleetObjectNo.

    Campos generados según el contrato de showObjectReport real de Webfleet.
    """
    from flask import current_app
    from app.models.vehicle import Vehicle

    try:
        org_id = None
        vehicles_db = Vehicle.query.filter(Vehicle.webfleetObjectNo.isnot(None)).all()
        if object_no:
            vehicles_db = [v for v in vehicles_db if v.webfleetObjectNo == object_no]
    except Exception:
        vehicles_db = []

    now = datetime.utcnow()
    rows = []
    for v in vehicles_db:
        seed = sum(ord(c) for c in (v.webfleetObjectNo or "MOCK"))
        rng = random.Random(seed + int(now.timestamp() // 600))  # cambia cada 10 min

        lat = _BASE_LAT + rng.uniform(-0.05, 0.05)
        lon = _BASE_LON + rng.uniform(-0.05, 0.05)
        speed = rng.choice([0, 0, 15, 30, 45, 60])
        ignition = 1 if speed > 0 else rng.choice([0, 1])

        rows.append({
            "objectno":        v.webfleetObjectNo,
            "objectname":      v.name,
            "objectclassname": v.type.value if v.type else "FIRE_TRUCK",
            "pos_latitude":    round(lat, 6),
            "pos_longitude":   round(lon, 6),
            "pos_altitude":    round(rng.uniform(600, 700), 1),
            "pos_time":        now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "pos_speed":       speed,
            "pos_course":      rng.randint(0, 359),
            "pos_text":        "Ctra. de Valencia, Madrid (demo)",
            "driver_name":     rng.choice(["Sin conductor", "Conductor A", "Conductor B"]),
            "driver_no":       "",
            "ignition_state":  ignition,
            "vehicle_state":   "active" if ignition else "inactive",
            "odometer_value":  round(12000 + seed * 3.7, 0),
            "msg_time":        now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "_mock":           True,
        })
    return rows


def show_digital_events(
    object_no: str,
    range_from: datetime,
    range_to: datetime,
) -> list[dict]:
    """
    Genera eventos de entrada digital sintéticos (rotativo ON/OFF) para demo.

    Imita la estructura de una respuesta de Webfleet showIOActivities:
        msg_time   ISO timestamp del cambio de estado
        input_no   número de canal digital (1 = rotativo)
        input_value "1" (ON) | "0" (OFF)
    """
    duration_s = max(0, int((range_to - range_from).total_seconds()))
    if duration_s == 0:
        return []

    seed = sum(ord(c) for c in (object_no or "MOCK"))
    n_events = 3 + (seed % 5)
    step = max(1, duration_s // (n_events + 1))

    rows: list[dict] = []
    state = True  # arranca en ON
    for i in range(n_events):
        offset = step * (i + 1) + (seed * (i + 1)) % max(1, step // 4)
        ts = range_from + timedelta(seconds=min(offset, duration_s - 1))
        rows.append({
            "msg_time": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "input_no": 1,
            "input_value": "1" if state else "0",
            "objectno": object_no,
            "_mock": True,
        })
        state = not state
    return rows
