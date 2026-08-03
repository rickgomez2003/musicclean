from datetime import UTC, datetime
from pathlib import Path

import pytest

from musicclean.orion.adapters.filesystem import LocalFilesystemMutator
from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import (
    BeginIdempotentOperation,
    ConflictError,
    CoordinatedExecution,
    begin_idempotent_operation,
    execute_quarantine_coordinated,
)
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
from musicclean.orion.shared import Confidence, EntityId, FrozenClock


def _seed_plan(db_path: Path, source: Path, target: Path) -> ActionPlan:
    subject_id = EntityId.new()
    evidence = EvidenceRecord(
        subject_id=subject_id,
        kind=EvidenceKind.TITLE,
        value="Track",
        provenance=EvidenceProvenance(
            provider="test",
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
        rationale="Review metadata.",
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
        source_location=str(source),
        target_location=str(target),
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


def test_duplicate_coordinated_quarantine_returns_existing_result(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "orion.db"
    source = tmp_path / "music" / "a.flac"
    target = tmp_path / "quarantine" / "a.flac"
    source.parent.mkdir()
    source.write_bytes(b"audio")
    plan = _seed_plan(db_path, source, target)

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    command = CoordinatedExecution(
        action_plan_id=plan.id,
        operator="operator",
        idempotency_key="quarantine-123",
        lease_owner="worker-a",
    )
    filesystem = LocalFilesystemMutator()
    clock = FrozenClock(datetime(2026, 8, 3, 1, 0, tzinfo=UTC))

    first = execute_quarantine_coordinated(command, filesystem, clock, factory)
    second = execute_quarantine_coordinated(command, filesystem, clock, factory)

    assert first == second
    assert target.read_bytes() == b"audio"


def test_idempotency_key_collision_is_rejected(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    source = tmp_path / "music" / "a.flac"
    target = tmp_path / "quarantine" / "a.flac"
    source.parent.mkdir()
    source.write_bytes(b"audio")
    plan = _seed_plan(db_path, source, target)

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    filesystem = LocalFilesystemMutator()
    clock = FrozenClock(datetime(2026, 8, 3, 1, 0, tzinfo=UTC))

    execute_quarantine_coordinated(
        CoordinatedExecution(
            plan.id,
            "operator",
            "shared-key",
            "worker-a",
        ),
        filesystem,
        clock,
        factory,
    )

    with pytest.raises(ConflictError, match="different operation"):
        begin_idempotent_operation(
            BeginIdempotentOperation(
                key="shared-key",
                operation="restore-quarantine",
                subject_id=plan.id,
            ),
            clock,
            factory,
        )
