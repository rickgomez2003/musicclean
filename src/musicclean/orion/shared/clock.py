"""Clock abstractions for deterministic time handling."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Port for obtaining the current UTC timestamp."""

    def now(self) -> datetime:
        """Return an aware UTC datetime."""


class SystemClock:
    """Production clock using the system UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock:
    """Deterministic clock useful for tests and replayable workflows."""

    def __init__(self, instant: datetime) -> None:
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError("FrozenClock requires a timezone-aware datetime")
        self._instant = instant.astimezone(UTC)

    def now(self) -> datetime:
        return self._instant
