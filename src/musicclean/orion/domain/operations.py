"""Operational hardening primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from musicclean.orion.domain._validation import require_text
from musicclean.orion.shared import EntityId


class IdempotencyStatus(StrEnum):
    STARTED = "started"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    """Persisted command de-duplication state."""

    key: str
    operation: str
    subject_id: EntityId
    status: IdempotencyStatus
    created_at: datetime
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", require_text(self.key, "idempotency key"))
        object.__setattr__(self, "operation", require_text(self.operation, "operation"))
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        object.__setattr__(self, "created_at", self.created_at.astimezone(UTC))
        if self.completed_at is not None:
            if self.completed_at.tzinfo is None or self.completed_at.utcoffset() is None:
                raise ValueError("completed_at must be timezone-aware")
            object.__setattr__(
                self,
                "completed_at",
                self.completed_at.astimezone(UTC),
            )


@dataclass(frozen=True, slots=True)
class ActionPlanLease:
    """Time-bounded exclusive lease for one ActionPlan."""

    action_plan_id: EntityId
    owner: str
    acquired_at: datetime
    expires_at: datetime
    id: EntityId = field(default_factory=EntityId.new)

    def __post_init__(self) -> None:
        object.__setattr__(self, "owner", require_text(self.owner, "owner"))
        for field_name in ("acquired_at", "expires_at"):
            value = getattr(self, field_name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{field_name} must be timezone-aware")
            object.__setattr__(self, field_name, value.astimezone(UTC))
        if self.expires_at <= self.acquired_at:
            raise ValueError("expires_at must be after acquired_at")

    def is_active_at(self, when: datetime) -> bool:
        if when.tzinfo is None or when.utcoffset() is None:
            raise ValueError("when must be timezone-aware")
        return when.astimezone(UTC) < self.expires_at
