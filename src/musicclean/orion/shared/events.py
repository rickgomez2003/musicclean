"""Base domain-event contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


def _utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Base class for immutable, timestamped domain events."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        object.__setattr__(self, "occurred_at", self.occurred_at.astimezone(UTC))
