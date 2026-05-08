"""Circuit breaker in-memory para Webfleet.

Estados:
    CLOSED:    requests pasan normal.
    OPEN:      requests rechazados sin llamar a Webfleet (cooldown activo).
    HALF_OPEN: tras cooldown, próxima request es de prueba; éxito vuelve a CLOSED.

Thresholds desde config:
    WEBFLEET_CB_FAIL_THRESHOLD (default 3)
    WEBFLEET_CB_COOLDOWN_S     (default 60)
"""
import time
from threading import Lock

from flask import current_app
from loguru import logger


class CircuitBreaker:
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self):
        self._state = self.CLOSED
        self._fail_count = 0
        self._opened_at = 0.0
        self._lock = Lock()

    def _threshold(self) -> int:
        return int(current_app.config.get("WEBFLEET_CB_FAIL_THRESHOLD", 3))

    def _cooldown(self) -> float:
        return float(current_app.config.get("WEBFLEET_CB_COOLDOWN_S", 60))

    def state(self) -> str:
        with self._lock:
            self._tick()
            return self._state

    def allow_request(self) -> bool:
        """True si la request puede proceder; False si CB está OPEN."""
        with self._lock:
            self._tick()
            return self._state in (self.CLOSED, self.HALF_OPEN)

    def record_success(self):
        with self._lock:
            if self._state in (self.HALF_OPEN, self.OPEN):
                logger.info("Webfleet CB: SUCCESS → CLOSED")
            self._state = self.CLOSED
            self._fail_count = 0
            self._opened_at = 0.0

    def record_failure(self):
        with self._lock:
            self._fail_count += 1
            threshold = self._threshold()
            if self._state == self.HALF_OPEN:
                logger.warning("Webfleet CB: HALF_OPEN failure → OPEN")
                self._state = self.OPEN
                self._opened_at = time.monotonic()
            elif self._fail_count >= threshold and self._state == self.CLOSED:
                logger.warning(
                    "Webfleet CB: %s fallos consecutivos → OPEN por %.0fs",
                    self._fail_count, self._cooldown(),
                )
                self._state = self.OPEN
                self._opened_at = time.monotonic()

    def _tick(self):
        """Transición OPEN → HALF_OPEN si pasó el cooldown."""
        if self._state == self.OPEN:
            elapsed = time.monotonic() - self._opened_at
            if elapsed >= self._cooldown():
                logger.info("Webfleet CB: cooldown vencido → HALF_OPEN")
                self._state = self.HALF_OPEN
                self._fail_count = 0
