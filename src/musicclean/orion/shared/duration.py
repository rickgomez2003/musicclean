"""Audio duration value object."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.shared.errors import DomainValidationError


@dataclass(frozen=True, slots=True, order=True)
class Duration:
    """Non-negative media duration stored as integer milliseconds."""

    milliseconds: int

    def __post_init__(self) -> None:
        if isinstance(self.milliseconds, bool) or self.milliseconds < 0:
            raise DomainValidationError("duration must be a non-negative integer")

    @classmethod
    def from_seconds(cls, seconds: float) -> Duration:
        """Create a Duration from seconds, rounded to the nearest millisecond."""
        if seconds < 0:
            raise DomainValidationError("duration cannot be negative")
        return cls(round(seconds * 1000))

    @property
    def seconds(self) -> float:
        return self.milliseconds / 1000.0
