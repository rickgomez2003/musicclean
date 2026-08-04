"""In-process runtime metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass(slots=True)
class RuntimeMetrics:
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)
    _requests: int = 0
    _errors: int = 0
    _duration_ms_total: float = 0.0

    def record_request(self, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self._requests += 1
            if status_code >= 400:
                self._errors += 1
            self._duration_ms_total += duration_ms

    def snapshot(self) -> dict[str, int | float]:
        with self._lock:
            average = self._duration_ms_total / self._requests if self._requests else 0.0
            return {
                "requests_total": self._requests,
                "errors_total": self._errors,
                "request_duration_ms_total": round(self._duration_ms_total, 3),
                "request_duration_ms_average": round(average, 3),
            }
