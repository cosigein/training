"""Integración con Webfleet.connect (D-WF-001).

Capas:
- client.py:          HTTP + auth (URL-encode UTF-8 del username con tilde) + show_tracks.
- circuit_breaker.py: protege contra caídas de Webfleet (CLOSED/OPEN/HALF_OPEN).
- rate_limiter.py:    respeta la cuota de 14.400 req/día con alertas a 70/85/95%.
- normalizer.py:      response → lista de dicts compatibles con GpsMeasurement.
- mapper.py:          Vehicle.webfleetObjectNo ↔ Webfleet objectno.
- sync.py:            orquesta cliente + normalizer + persistencia para un Attempt.
- mock.py:            fallback si faltan credenciales o WEBFLEET_ENABLED=false.

Punto de entrada típico: `from app.services.webfleet.sync import sync_attempt_gps`.
"""
from .sync import (
    sync_attempt_gps,
    sync_attempt_rotativo,
    get_attempt_data_status,
    check_and_autoclose,
    WebfleetSyncError,
)

__all__ = [
    "sync_attempt_gps",
    "sync_attempt_rotativo",
    "get_attempt_data_status",
    "check_and_autoclose",
    "WebfleetSyncError",
]
