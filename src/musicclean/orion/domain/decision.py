"""Explainable recommendations derived from Knowledge."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from musicclean.orion.domain._validation import optional_text, require_text
from musicclean.orion.shared import Confidence, EntityId


class DecisionAction(StrEnum):
    """Initial non-destructive Orion recommendation actions."""

    KEEP = "keep"
    REVIEW = "review"
    REPAIR_METADATA = "repair_metadata"
    REANALYZE = "reanalyze"
    IGNORE = "ignore"


@dataclass(frozen=True, slots=True)
class Decision:
    """Immutable, explainable recommendation derived from Knowledge."""

    subject_id: EntityId
    action: DecisionAction
    confidence: Confidence
    rationale: str
    knowledge_ids: tuple[EntityId, ...]
    rule_id: str
    rule_version: str
    decided_at: datetime
    risk: str | None = None
    id: EntityId = field(default_factory=EntityId.new)

    def __post_init__(self) -> None:
        object.__setattr__(self, "rationale", require_text(self.rationale, "rationale"))
        object.__setattr__(self, "rule_id", require_text(self.rule_id, "rule id"))
        object.__setattr__(
            self,
            "rule_version",
            require_text(self.rule_version, "rule version"),
        )
        object.__setattr__(self, "risk", optional_text(self.risk))

        if not self.knowledge_ids:
            raise ValueError("decision requires at least one knowledge id")
        if self.decided_at.tzinfo is None or self.decided_at.utcoffset() is None:
            raise ValueError("decided_at must be timezone-aware")
        object.__setattr__(self, "decided_at", self.decided_at.astimezone(UTC))
