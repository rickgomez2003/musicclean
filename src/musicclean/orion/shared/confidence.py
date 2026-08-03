"""Confidence value object."""

from __future__ import annotations

from dataclasses import dataclass

from musicclean.orion.shared.errors import DomainValidationError


@dataclass(frozen=True, slots=True, order=True)
class Confidence:
    """Normalized confidence score in the inclusive range [0.0, 1.0]."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise DomainValidationError("confidence must be between 0.0 and 1.0")

    @classmethod
    def from_percent(cls, percent: float) -> Confidence:
        """Build a confidence score from a percentage in [0, 100]."""
        if not 0.0 <= percent <= 100.0:
            raise DomainValidationError("percent must be between 0 and 100")
        return cls(percent / 100.0)

    @property
    def percent(self) -> float:
        """Return the confidence score as a percentage."""
        return self.value * 100.0
