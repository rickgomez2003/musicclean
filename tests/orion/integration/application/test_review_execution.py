from datetime import UTC, datetime
from pathlib import Path

import pytest

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import (
    AuthorizeDecision,
    ConflictError,
    PlanQuarantine,
    ReviewDecision,
    authorize_decision,
    plan_quarantine,
    review_decision,
)
from musicclean.orion.domain import (
    AudioFile,
    Decision,
    DecisionAction,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceRecord,
    KnowledgeFact,
    KnowledgeKind,
    ReviewOutcome,
)
from musicclean.orion.shared import ByteSize, Confidence, FrozenClock


def _seed_reviewable_decision(db_path: Path) -> Decision:
    audio_file = AudioFile(location="/music/a.flac", size=ByteSize(100))
    evidence = EvidenceRecord(
        subject_id=audio_file.id,
        kind=EvidenceKind.TITLE,
        value="Track",
        provenance=EvidenceProvenance(
            provider="test",
            observed_at=datetime(2026, 8, 3, tzinfo=UTC),
        ),
    )
    knowledge = KnowledgeFact(
        subject_id=audio_file.id,
        kind=KnowledgeKind.CORE_METADATA_COMPLETE,
        value=False,
        confidence=Confidence(1.0),
        evidence_ids=(evidence.id,),
        rule_id="metadata.core-complete",
        rule_version="1",
        inferred_at=datetime(2026, 8, 3, tzinfo=UTC),
    )
    decision = Decision(
        subject_id=audio_file.id,
        action=DecisionAction.REPAIR_METADATA,
        confidence=Confidence(1.0),
        rationale="Metadata needs review.",
        knowledge_ids=(knowledge.id,),
        rule_id="decision.metadata-repair",
        rule_version="1",
        decided_at=datetime(2026, 8, 3, tzinfo=UTC),
    )
    with SqliteUnitOfWork(db_path) as uow:
        uow.audio_files.save(audio_file)
        uow.evidence.save(evidence)
        uow.knowledge.save(knowledge)
        uow.decisions.save(decision)
        uow.commit()
    return decision


def test_authorization_requires_approved_review(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    decision = _seed_reviewable_decision(db_path)
    clock = FrozenClock(datetime(2026, 8, 3, 1, 0, tzinfo=UTC))

    with pytest.raises(ConflictError):
        authorize_decision(
            AuthorizeDecision(decision.id, "operator"),
            clock,
            lambda: SqliteUnitOfWork(db_path),
        )


def test_quarantine_plan_requires_review_and_authorization(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    decision = _seed_reviewable_decision(db_path)
    clock = FrozenClock(datetime(2026, 8, 3, 1, 0, tzinfo=UTC))

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    review = review_decision(
        ReviewDecision(
            decision.id,
            ReviewOutcome.APPROVED,
            "reviewer",
            "Approved for quarantine planning.",
        ),
        clock,
        factory,
    )
    grant = authorize_decision(
        AuthorizeDecision(decision.id, "operator"),
        clock,
        factory,
    )
    planned = plan_quarantine(
        PlanQuarantine(
            decision.id,
            "/music/a.flac",
            "/quarantine/a.flac",
        ),
        clock,
        factory,
    )

    assert grant.review_id == review.id
    assert planned.plan.authorization_id == grant.id
    assert planned.undo.restore_from == "/quarantine/a.flac"
    assert planned.undo.restore_to == "/music/a.flac"

    with SqliteUnitOfWork(db_path) as uow:
        persisted = uow.action_plans.get(planned.plan.id)
    assert persisted == planned.plan
