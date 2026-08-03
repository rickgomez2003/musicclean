"""Operator-approved reconciliation recovery model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from musicclean.orion.domain._validation import optional_text, require_text
from musicclean.orion.shared import EntityId


class RecoveryKind(StrEnum):
    QUARANTINE_AUDIT = "quarantine_audit"
    RESTORE_AUDIT = "restore_audit"


@dataclass(frozen=True, slots=True)
class RecoveryApproval:
    """Explicit approval to repair one reconciliation finding."""

    finding_id: EntityId
    kind: RecoveryKind
    approved_by: str
    approved_at: datetime
    note: str | None = None
    id: EntityId = field(default_factory=EntityId.new)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "approved_by",
            require_text(self.approved_by, "approved by"),
        )
        object.__setattr__(self, "note", optional_text(self.note))
        if self.approved_at.tzinfo is None or self.approved_at.utcoffset() is None:
            raise ValueError("approved_at must be timezone-aware")
        object.__setattr__(self, "approved_at", self.approved_at.astimezone(UTC))


@dataclass(frozen=True, slots=True)
class RecoveryRecord:
    """Audit record showing an approved recovery was applied."""

    finding_id: EntityId
    approval_id: EntityId
    execution_id: EntityId
    kind: RecoveryKind
    recovered_by: str
    recovered_at: datetime
    id: EntityId = field(default_factory=EntityId.new)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "recovered_by",
            require_text(self.recovered_by, "recovered by"),
        )
        if self.recovered_at.tzinfo is None or self.recovered_at.utcoffset() is None:
            raise ValueError("recovered_at must be timezone-aware")
        object.__setattr__(self, "recovered_at", self.recovered_at.astimezone(UTC))
