"""Rate limiter in-memory para la cuota diaria de Webfleet (D-WF-001).

CMadrid tiene 14.400 req/día. Llevamos un contador por día (UTC) y emitimos
warnings al cruzar 70%, 85% y 95% para que ops se entere antes de toparse.

Cuando se rebasa el 100%, `try_acquire` devuelve False y el cliente lanza
WebfleetError. El contador se resetea automáticamente al cambiar el día UTC.
"""
from datetime import datetime, timezone
from threading import Lock

from flask import current_app
from loguru import logger


class RateLimiter:
    def __init__(self):
        self._day = self._today()
        self._count = 0
        self._alerted = set()
        self._lock = Lock()

    @staticmethod
    def _today() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _quota(self) -> int:
        return int(current_app.config.get("WEBFLEET_DAILY_QUOTA", 14400))

    def try_acquire(self) -> bool:
        """Reserva 1 token; devuelve False si ya se rebasó la cuota del día."""
        with self._lock:
            today = self._today()
            if today != self._day:
                self._day = today
                self._count = 0
                self._alerted.clear()

            quota = self._quota()
            if self._count >= quota:
                logger.error("Webfleet rate limit: cuota %s rebasada (día %s)", quota, self._day)
                return False

            self._count += 1

            ratio = self._count / quota
            for threshold in (0.70, 0.85, 0.95):
                if ratio >= threshold and threshold not in self._alerted:
                    self._alerted.add(threshold)
                    logger.warning(
                        "Webfleet rate limit: %.0f%% de cuota usada (%s / %s)",
                        threshold * 100, self._count, quota,
                    )
            return True

    def usage(self) -> tuple[int, int]:
        with self._lock:
            return (self._count, self._quota())
