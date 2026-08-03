"""Crash-recovery reconciliation model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from musicclean.orion.domain._validation import require_text
from musicclean.orion.shared import EntityId


class ReconciliationStatus(StrEnum):
    """Observed relationship between filesystem state and execution audit."""

    CONSISTENT_ACTIVE = "consistent_active"
    CONSISTENT_QUARANTINED = "consistent_quarantined"
    CONSISTENT_RESTORED = "consistent_restored"
    AUDIT_MISSING_AFTER_QUARANTINE = "audit_missing_after_quarantine"
    AUDIT_MISSING_AFTER_RESTORE = "audit_missing_after_restore"
    AMBIGUOUS_BOTH_EXIST = "ambiguous_both_exist"
    MISSING_BOTH = "missing_both"


class ReconciliationAction(StrEnum):
    """Safe next step proposed by reconciliation."""

    NONE = "none"
    REVIEW = "review"
    RECOVER_QUARANTINE_AUDIT = "recover_quarantine_audit"
    RECOVER_RESTORE_AUDIT = "recover_restore_audit"


@dataclass(frozen=True, slots=True)
class ReconciliationFinding:
    """Immutable snapshot of a reconciliation check."""

    action_plan_id: EntityId
    status: ReconciliationStatus
    proposed_action: ReconciliationAction
    source_exists: bool
    target_exists: bool
    has_quarantine_audit: bool
    has_restore_audit: bool
    detail: str
    checked_at: datetime
    id: EntityId = field(default_factory=EntityId.new)

    def __post_init__(self) -> None:
        object.__setattr__(self, "detail", require_text(self.detail, "detail"))
        if self.checked_at.tzinfo is None or self.checked_at.utcoffset() is None:
            raise ValueError("checked_at must be timezone-aware")
        object.__setattr__(self, "checked_at", self.checked_at.astimezone(UTC))
