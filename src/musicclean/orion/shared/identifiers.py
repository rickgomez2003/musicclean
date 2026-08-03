"""Stable internal identifiers for Orion domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class EntityId:
    """Stable internal identity independent of filesystem location."""

    value: UUID

    @classmethod
    def new(cls) -> EntityId:
        """Create a new random entity identifier."""
        return cls(uuid4())

    @classmethod
    def parse(cls, value: str | UUID) -> EntityId:
        """Parse a UUID or UUID string into an EntityId."""
        return cls(value if isinstance(value, UUID) else UUID(value))

    def __str__(self) -> str:
        return str(self.value)
