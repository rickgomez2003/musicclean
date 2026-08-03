from datetime import UTC, datetime

from musicclean.orion.application import (
    HighResolutionReviewRule,
    MetadataRepairRecommendationRule,
)
from musicclean.orion.domain import (
    DecisionAction,
    KnowledgeFact,
    KnowledgeKind,
)
from musicclean.orion.shared import Confidence, EntityId


def _fact(
    subject: EntityId,
    kind: KnowledgeKind,
    value: bool,
) -> KnowledgeFact:
    return KnowledgeFact(
        subject_id=subject,
        kind=kind,
        value=value,
        confidence=Confidence(1.0),
        evidence_ids=(EntityId.new(),),
        rule_id="test",
        rule_version="1",
        inferred_at=datetime(2026, 8, 3, tzinfo=UTC),
    )


def test_metadata_repair_rule_recommends_repair_when_incomplete() -> None:
    subject = EntityId.new()
    decision = MetadataRepairRecommendationRule().decide(
        subject,
        (_fact(subject, KnowledgeKind.CORE_METADATA_COMPLETE, False),),
        datetime.now(UTC),
    )
    assert decision is not None
    assert decision.action is DecisionAction.REPAIR_METADATA


def test_metadata_repair_rule_keeps_when_complete() -> None:
    subject = EntityId.new()
    decision = MetadataRepairRecommendationRule().decide(
        subject,
        (_fact(subject, KnowledgeKind.CORE_METADATA_COMPLETE, True),),
        datetime.now(UTC),
    )
    assert decision is not None
    assert decision.action is DecisionAction.KEEP


def test_high_resolution_rule_recommends_review_not_delete() -> None:
    subject = EntityId.new()
    decision = HighResolutionReviewRule().decide(
        subject,
        (_fact(subject, KnowledgeKind.HIGH_RESOLUTION_FORMAT, True),),
        datetime.now(UTC),
    )
    assert decision is not None
    assert decision.action is DecisionAction.REVIEW
