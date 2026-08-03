"""Deterministic Knowledge-to-Decision recommendation rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from musicclean.orion.domain import (
    Decision,
    DecisionAction,
    KnowledgeFact,
    KnowledgeKind,
)
from musicclean.orion.shared import Confidence, EntityId


class DecisionRule(Protocol):
    """Contract for deriving a recommendation from Knowledge."""

    @property
    def rule_id(self) -> str: ...

    @property
    def rule_version(self) -> str: ...

    def decide(
        self,
        subject_id: EntityId,
        knowledge: tuple[KnowledgeFact, ...],
        decided_at: datetime,
    ) -> Decision | None: ...


def latest_knowledge_by_kind(
    knowledge: tuple[KnowledgeFact, ...],
) -> dict[KnowledgeKind, KnowledgeFact]:
    """Return the newest Knowledge fact for each kind."""
    latest: dict[KnowledgeKind, KnowledgeFact] = {}
    for fact in knowledge:
        existing = latest.get(fact.kind)
        if existing is None or fact.inferred_at > existing.inferred_at:
            latest[fact.kind] = fact
    return latest


@dataclass(frozen=True, slots=True)
class MetadataRepairRecommendationRule:
    """Recommend metadata repair when core metadata is known incomplete."""

    rule_id: str = "decision.metadata-repair"
    rule_version: str = "1"

    def decide(
        self,
        subject_id: EntityId,
        knowledge: tuple[KnowledgeFact, ...],
        decided_at: datetime,
    ) -> Decision | None:
        latest = latest_knowledge_by_kind(knowledge)
        fact = latest.get(KnowledgeKind.CORE_METADATA_COMPLETE)
        if fact is None or not isinstance(fact.value, bool):
            return None

        if fact.value:
            return Decision(
                subject_id=subject_id,
                action=DecisionAction.KEEP,
                confidence=fact.confidence,
                rationale="Core title, artist, and album metadata are complete.",
                knowledge_ids=(fact.id,),
                rule_id=self.rule_id,
                rule_version=self.rule_version,
                decided_at=decided_at,
                risk="No destructive action is proposed.",
            )

        return Decision(
            subject_id=subject_id,
            action=DecisionAction.REPAIR_METADATA,
            confidence=fact.confidence,
            rationale="Core metadata is incomplete and should be reviewed or repaired.",
            knowledge_ids=(fact.id,),
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            decided_at=decided_at,
            risk="Metadata changes should be reviewed before writing to media files.",
        )


@dataclass(frozen=True, slots=True)
class HighResolutionReviewRule:
    """Recommend review of technically high-resolution files.

    This rule deliberately does not infer mastering quality or authenticity.
    """

    rule_id: str = "decision.high-resolution-review"
    rule_version: str = "1"

    def decide(
        self,
        subject_id: EntityId,
        knowledge: tuple[KnowledgeFact, ...],
        decided_at: datetime,
    ) -> Decision | None:
        latest = latest_knowledge_by_kind(knowledge)
        fact = latest.get(KnowledgeKind.HIGH_RESOLUTION_FORMAT)
        if fact is None or fact.value is not True:
            return None

        return Decision(
            subject_id=subject_id,
            action=DecisionAction.REVIEW,
            confidence=Confidence(1.0),
            rationale=(
                "The file meets Orion's technical high-resolution format threshold; "
                "future analysis may evaluate provenance or upsampling."
            ),
            knowledge_ids=(fact.id,),
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            decided_at=decided_at,
            risk="Technical format classification does not imply superior sound quality.",
        )


DEFAULT_DECISION_RULES: tuple[DecisionRule, ...] = (
    MetadataRepairRecommendationRule(),
    HighResolutionReviewRule(),
)
