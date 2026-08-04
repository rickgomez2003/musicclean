"""Production clock implementation."""

from __future__ import annotations

from datetime import UTC, datetime


class UtcSystemClock:
    """Return timezone-aware UTC timestamps."""

    def now(self) -> datetime:
        return datetime.now(UTC)
