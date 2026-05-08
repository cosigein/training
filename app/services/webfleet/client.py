"""Cliente HTTP de Webfleet.connect.

Auth: account + username + password + apikey por query string (legacy).
Output: JSON cuando se pasa `outputformat=json`.

GOTCHA conocido (memory/decision-webfleet-entra.md:34): el username de
CMadrid lleva una tilde. Si se manda sin URL-encode UTF-8, la API responde
401 sin mensaje útil. `urllib.parse.quote` con default safe='' lo encodea
correctamente.

Si WEBFLEET_ENABLED=false o faltan credenciales, el cliente delega al
módulo mock. Esto permite desarrollar y hacer demo sin credenciales reales.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from urllib.parse import quote

import httpx
from flask import current_app
from loguru import logger

from .circuit_breaker import CircuitBreaker
from .rate_limiter import RateLimiter
from . import mock


class WebfleetError(Exception):
    """Error de comunicación o lógico con Webfleet."""

    def __init__(self, message: str, http_status: Optional[int] = None, code: Optional[str] = None):
        super().__init__(message)
        self.http_status = http_status
        self.code = code


# Singletons in-memory por proceso. En multi-worker (gunicorn) cada worker
# tiene su propio CB/RL — aceptable para esta cuota. Si se necesita global,
# migrar a Redis.
_circuit_breaker = CircuitBreaker()
_rate_limiter = RateLimiter()


def _is_real_mode() -> bool:
    cfg = current_app.config
    return bool(
        cfg.get("WEBFLEET_ENABLED")
        and cfg.get("WEBFLEET_ACCOUNT")
        and cfg.get("WEBFLEET_USERNAME")
        and cfg.get("WEBFLEET_PASSWORD")
        and cfg.get("WEBFLEET_APIKEY")
    )


def _build_auth_params() -> dict:
    cfg = current_app.config
    # URL-encoded UTF-8 — CRÍTICO para usernames con tilde.
    return {
        "account": cfg["WEBFLEET_ACCOUNT"],
        "username": quote(cfg["WEBFLEET_USERNAME"], safe=""),
        "password": cfg["WEBFLEET_PASSWORD"],
        "apikey": cfg["WEBFLEET_APIKEY"],
        "lang": "es",
        "outputformat": "json",
    }


def show_tracks(
    object_no: str,
    range_from: datetime,
    range_to: datetime,
    timeout_s: float = 15.0,
) -> list[dict]:
    """
    Pide el histórico de posiciones de un vehículo a Webfleet.connect.

    Args:
        object_no:  identificador del vehículo en Webfleet (Vehicle.webfleetObjectNo).
        range_from: inicio del rango (UTC).
        range_to:   fin del rango (UTC).
        timeout_s:  timeout HTTP.

    Returns:
        Lista de dicts crudos (formato Webfleet show_tracks). El normalizer
        los convierte a GpsMeasurement.

    Raises:
        WebfleetError: si auth, red, circuit breaker o rate limit fallan.
    """
    if not _is_real_mode():
        logger.info("Webfleet client en modo MOCK (sin credenciales reales)")
        return mock.show_tracks(object_no, range_from, range_to)

    if not _circuit_breaker.allow_request():
        raise WebfleetError(
            "Webfleet circuit breaker OPEN — fallback a sensor",
            code="circuit_open",
        )

    if not _rate_limiter.try_acquire():
        raise WebfleetError(
            "Cuota diaria de Webfleet agotada",
            code="rate_limit",
        )

    cfg = current_app.config
    base_url = cfg["WEBFLEET_BASE_URL"]
    params = _build_auth_params()
    params["action"] = "showTracks"
    params["objectno"] = object_no
    params["range_pattern"] = "ud"  # user-defined range
    params["rangefrom_string"] = range_from.strftime("%Y-%m-%d %H:%M:%S")
    params["rangeto_string"] = range_to.strftime("%Y-%m-%d %H:%M:%S")

    try:
        with httpx.Client(timeout=timeout_s) as client:
            resp = client.get(base_url, params=params)
    except httpx.RequestError as exc:
        _circuit_breaker.record_failure()
        raise WebfleetError(f"Webfleet network error: {exc}", code="network") from exc

    if resp.status_code >= 500:
        _circuit_breaker.record_failure()
        raise WebfleetError(
            f"Webfleet server error {resp.status_code}",
            http_status=resp.status_code,
            code="server_error",
        )

    if resp.status_code == 401:
        _circuit_breaker.record_failure()
        raise WebfleetError(
            "Webfleet 401 — verificar credenciales y URL-encoding del username",
            http_status=401,
            code="auth_failed",
        )

    if resp.status_code >= 400:
        # Errores 4xx no abren el CB (son problemas de payload, no caída).
        raise WebfleetError(
            f"Webfleet client error {resp.status_code}: {resp.text[:200]}",
            http_status=resp.status_code,
            code="client_error",
        )

    _circuit_breaker.record_success()

    try:
        data = resp.json()
    except ValueError as exc:
        raise WebfleetError("Webfleet response no es JSON válido", code="bad_response") from exc

    # show_tracks devuelve una lista directamente (en outputformat=json).
    # Algunos endpoints envuelven en un dict — defensa.
    if isinstance(data, dict):
        data = data.get("data", data.get("rows", []))
    if not isinstance(data, list):
        return []

    return data


def show_digital_events(
    object_no: str,
    range_from: datetime,
    range_to: datetime,
    input_no: int = 1,
    timeout_s: float = 15.0,
) -> list[dict]:
    """
    Pide activaciones de entradas digitales del vehículo (ej: rotativo de emergencia).

    En modo real llama a `showIOActivities` de Webfleet.connect.
    En mock genera eventos sintéticos ON/OFF.

    Args:
        object_no:  identificador del vehículo en Webfleet.
        range_from: inicio del rango (UTC).
        range_to:   fin del rango (UTC).
        input_no:   número de canal digital (1 = rotativo por convención CMadrid).
        timeout_s:  timeout HTTP.

    Returns:
        Lista de dicts con: msg_time, input_no, input_value, objectno.
    """
    if not _is_real_mode():
        logger.info("Webfleet client en modo MOCK para showIOActivities")
        return mock.show_digital_events(object_no, range_from, range_to)

    if not _circuit_breaker.allow_request():
        raise WebfleetError("Webfleet circuit breaker OPEN", code="circuit_open")

    if not _rate_limiter.try_acquire():
        raise WebfleetError("Cuota diaria de Webfleet agotada", code="rate_limit")

    cfg = current_app.config
    base_url = cfg["WEBFLEET_BASE_URL"]
    params = _build_auth_params()
    params["action"] = "showIOActivities"
    params["objectno"] = object_no
    params["range_pattern"] = "ud"
    params["rangefrom_string"] = range_from.strftime("%Y-%m-%d %H:%M:%S")
    params["rangeto_string"] = range_to.strftime("%Y-%m-%d %H:%M:%S")
    params["inputno"] = str(input_no)

    try:
        with httpx.Client(timeout=timeout_s) as client:
            resp = client.get(base_url, params=params)
    except httpx.RequestError as exc:
        _circuit_breaker.record_failure()
        raise WebfleetError(f"Webfleet network error: {exc}", code="network") from exc

    if resp.status_code >= 500:
        _circuit_breaker.record_failure()
        raise WebfleetError(f"Webfleet server error {resp.status_code}", http_status=resp.status_code, code="server_error")

    if resp.status_code == 401:
        _circuit_breaker.record_failure()
        raise WebfleetError("Webfleet 401 — verificar credenciales", http_status=401, code="auth_failed")

    if resp.status_code == 404 or resp.status_code == 400:
        # showIOActivities puede no estar disponible en todas las cuentas — degradar a mock.
        logger.warning("Webfleet showIOActivities no disponible (%s) — fallback a mock", resp.status_code)
        return mock.show_digital_events(object_no, range_from, range_to)

    if resp.status_code >= 400:
        raise WebfleetError(f"Webfleet client error {resp.status_code}: {resp.text[:200]}", http_status=resp.status_code, code="client_error")

    _circuit_breaker.record_success()

    try:
        data = resp.json()
    except ValueError as exc:
        raise WebfleetError("Webfleet response no es JSON válido", code="bad_response") from exc

    if isinstance(data, dict):
        data = data.get("data", data.get("rows", []))
    if not isinstance(data, list):
        return []

    return data
