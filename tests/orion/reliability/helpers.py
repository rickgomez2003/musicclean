"""Shared builders for reliability scenarios."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.domain import (
    ActionPlan,
    AuthorizationGrant,
    Decision,
    DecisionAction,
    DecisionReview,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceRecord,
    KnowledgeFact,
    KnowledgeKind,
    PlannedAction,
    ReviewOutcome,
)
from musicclean.orion.shared import Confidence, EntityId


def seed_action_plan(
    db_path: Path,
    source_location: str,
    target_location: str,
) -> ActionPlan:
    subject_id = EntityId.new()
    evidence = EvidenceRecord(
        subject_id=subject_id,
        kind=EvidenceKind.TITLE,
        value="Track",
        provenance=EvidenceProvenance(
            provider="reliability-test",
            observed_at=datetime(2026, 8, 3, tzinfo=UTC),
        ),
    )
    knowledge = KnowledgeFact(
        subject_id=subject_id,
        kind=KnowledgeKind.CORE_METADATA_COMPLETE,
        value=False,
        confidence=Confidence(1.0),
        evidence_ids=(evidence.id,),
        rule_id="metadata.core-complete",
        rule_version="1",
        inferred_at=datetime(2026, 8, 3, tzinfo=UTC),
    )
    decision = Decision(
        subject_id=subject_id,
        action=DecisionAction.REPAIR_METADATA,
        confidence=Confidence(1.0),
        rationale="Reliability test.",
        knowledge_ids=(knowledge.id,),
        rule_id="decision.metadata-repair",
        rule_version="1",
        decided_at=datetime(2026, 8, 3, tzinfo=UTC),
    )
    review = DecisionReview(
        decision_id=decision.id,
        outcome=ReviewOutcome.APPROVED,
        reviewed_by="reviewer",
        reviewed_at=datetime(2026, 8, 3, tzinfo=UTC),
    )
    grant = AuthorizationGrant(
        decision_id=decision.id,
        review_id=review.id,
        granted_by="operator",
        granted_at=datetime(2026, 8, 3, tzinfo=UTC),
    )
    plan = ActionPlan(
        decision_id=decision.id,
        authorization_id=grant.id,
        action=PlannedAction.QUARANTINE,
        source_location=source_location,
        target_location=target_location,
        created_at=datetime(2026, 8, 3, tzinfo=UTC),
    )

    with SqliteUnitOfWork(db_path) as uow:
        uow.evidence.save(evidence)
        uow.knowledge.save(knowledge)
        uow.decisions.save(decision)
        uow.reviews.save(review)
        uow.authorizations.save(grant)
        uow.action_plans.save(plan)
        uow.commit()

    return plan
