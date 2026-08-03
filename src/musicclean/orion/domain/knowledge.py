"""Knowledge facts inferred from Evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from musicclean.orion.domain._validation import require_text
from musicclean.orion.shared import Confidence, EntityId

KnowledgeValue = str | int | float | bool


class KnowledgeKind(StrEnum):
    """Initial deterministic facts inferred by Orion."""

    CORE_METADATA_COMPLETE = "core_metadata_complete"
    HIGH_RESOLUTION_FORMAT = "high_resolution_format"


@dataclass(frozen=True, slots=True)
class KnowledgeFact:
    """Immutable fact inferred from one or more Evidence records."""

    subject_id: EntityId
    kind: KnowledgeKind
    value: KnowledgeValue
    confidence: Confidence
    evidence_ids: tuple[EntityId, ...]
    rule_id: str
    rule_version: str
    inferred_at: datetime
    id: EntityId = field(default_factory=EntityId.new)

    def __post_init__(self) -> None:
        object.__setattr__(self, "rule_id", require_text(self.rule_id, "rule id"))
        object.__setattr__(
            self,
            "rule_version",
            require_text(self.rule_version, "rule version"),
        )
        if not self.evidence_ids:
            raise ValueError("knowledge fact requires at least one evidence id")
        if self.inferred_at.tzinfo is None or self.inferred_at.utcoffset() is None:
            raise ValueError("inferred_at must be timezone-aware")
        object.__setattr__(self, "inferred_at", self.inferred_at.astimezone(UTC))
