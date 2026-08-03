"""Review, authorization, and execution-planning domain types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from musicclean.orion.domain._validation import optional_text, require_text
from musicclean.orion.shared import EntityId


class ReviewOutcome(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class DecisionReview:
    decision_id: EntityId
    outcome: ReviewOutcome
    reviewed_by: str
    reviewed_at: datetime
    note: str | None = None
    id: EntityId = field(default_factory=EntityId.new)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reviewed_by",
            require_text(self.reviewed_by, "reviewed by"),
        )
        object.__setattr__(self, "note", optional_text(self.note))
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise ValueError("reviewed_at must be timezone-aware")
        object.__setattr__(self, "reviewed_at", self.reviewed_at.astimezone(UTC))


@dataclass(frozen=True, slots=True)
class AuthorizationGrant:
    """Explicit authorization for one reviewed Decision."""

    decision_id: EntityId
    review_id: EntityId
    granted_by: str
    granted_at: datetime
    id: EntityId = field(default_factory=EntityId.new)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "granted_by",
            require_text(self.granted_by, "granted by"),
        )
        if self.granted_at.tzinfo is None or self.granted_at.utcoffset() is None:
            raise ValueError("granted_at must be timezone-aware")
        object.__setattr__(self, "granted_at", self.granted_at.astimezone(UTC))


class PlannedAction(StrEnum):
    QUARANTINE = "quarantine"


@dataclass(frozen=True, slots=True)
class ActionPlan:
    """Authorized but not yet executed filesystem action."""

    decision_id: EntityId
    authorization_id: EntityId
    action: PlannedAction
    source_location: str
    target_location: str
    created_at: datetime
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
        if self.source_location == self.target_location:
            raise ValueError("source and target locations must differ")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")
        object.__setattr__(self, "created_at", self.created_at.astimezone(UTC))


@dataclass(frozen=True, slots=True)
class UndoDescriptor:
    """Information required to reverse a future quarantine action."""

    action_plan_id: EntityId
    restore_from: str
    restore_to: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "restore_from",
            require_text(self.restore_from, "restore from"),
        )
        object.__setattr__(
            self,
            "restore_to",
            require_text(self.restore_to, "restore to"),
        )
