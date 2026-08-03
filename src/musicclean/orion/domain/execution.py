"""Auditable filesystem execution events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from musicclean.orion.domain._validation import require_text
from musicclean.orion.shared import EntityId


class ExecutionKind(StrEnum):
    """Reversible execution kinds supported by Orion."""

    QUARANTINE = "quarantine"
    RESTORE = "restore"


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    """Immutable audit record for one completed filesystem operation."""

    action_plan_id: EntityId
    kind: ExecutionKind
    source_location: str
    target_location: str
    executed_by: str
    executed_at: datetime
    id: EntityId = field(default_factory=EntityId.new)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_location",
            require_text(self.source_location, "source location"),
        )
        object.__setattr__(
            self,
            "target_location",
            require_text(self.target_location, "target location"),
        )
        object.__setattr__(
            self,
            "executed_by",
            require_text(self.executed_by, "executed by"),
        )
        if self.source_location == self.target_location:
            raise ValueError("execution source and target locations must differ")
        if self.executed_at.tzinfo is None or self.executed_at.utcoffset() is None:
            raise ValueError("executed_at must be timezone-aware")
        object.__setattr__(self, "executed_at", self.executed_at.astimezone(UTC))
