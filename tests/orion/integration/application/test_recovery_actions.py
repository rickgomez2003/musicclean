from datetime import UTC, datetime
from pathlib import Path

import pytest

from musicclean.orion.adapters.filesystem import LocalFilesystemMutator
from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import (
    ApplyRecovery,
    ApproveRecovery,
    AuthorizeDecision,
    ConflictError,
    PlanQuarantine,
    ReconcileActionPlan,
    ReviewDecision,
    apply_recovery,
    approve_recovery,
    authorize_decision,
    plan_quarantine,
    reconcile_action_plan,
    review_decision,
)
from musicclean.orion.domain import (
    AudioFile,
    Decision,
    DecisionAction,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceRecord,
    ExecutionKind,
    ExecutionOrigin,
    KnowledgeFact,
    KnowledgeKind,
    ReconciliationAction,
    ReviewOutcome,
)
from musicclean.orion.shared import ByteSize, Confidence, FrozenClock


def _seed_plan(db_path: Path, source: Path, target: Path):
    audio_file = AudioFile(location=str(source), size=ByteSize(source.stat().st_size))
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
        rationale="Review metadata.",
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

    clock = FrozenClock(datetime(2026, 8, 3, 1, 0, tzinfo=UTC))

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    review_decision(
        ReviewDecision(decision.id, ReviewOutcome.APPROVED, "reviewer"),
        clock,
        factory,
    )
    authorize_decision(
        AuthorizeDecision(decision.id, "operator"),
        clock,
        factory,
    )
    return plan_quarantine(
        PlanQuarantine(decision.id, str(source), str(target)),
        clock,
        factory,
    ).plan


def test_operator_approved_recovery_creates_recovered_execution_audit(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "orion.db"
    source = tmp_path / "music" / "a.flac"
    target = tmp_path / "quarantine" / "a.flac"
    source.parent.mkdir()
    source.write_bytes(b"audio")

    plan = _seed_plan(db_path, source, target)
    target.parent.mkdir()
    source.replace(target)

    filesystem = LocalFilesystemMutator()

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    finding = reconcile_action_plan(
        ReconcileActionPlan(plan.id),
        filesystem,
        FrozenClock(datetime(2026, 8, 3, 2, 0, tzinfo=UTC)),
        factory,
    )
    assert finding.proposed_action is ReconciliationAction.RECOVER_QUARANTINE_AUDIT

    approval = approve_recovery(
        ApproveRecovery(finding.id, "operator", "Crash confirmed."),
        FrozenClock(datetime(2026, 8, 3, 2, 1, tzinfo=UTC)),
        factory,
    )
    recovery = apply_recovery(
        ApplyRecovery(approval.id, "operator"),
        filesystem,
        FrozenClock(datetime(2026, 8, 3, 2, 2, tzinfo=UTC)),
        factory,
    )

    assert target.read_bytes() == b"audio"
    assert not source.exists()

    with SqliteUnitOfWork(db_path) as uow:
        execution = uow.executions.latest_for_plan_kind(
            plan.id,
            ExecutionKind.QUARANTINE,
        )
        recoveries = uow.recoveries.list_for_finding(finding.id)

    assert execution is not None
    assert execution.origin is ExecutionOrigin.RECOVERED
    assert execution.recovery_finding_id == finding.id
    assert recoveries == (recovery,)


def test_recovery_refuses_if_filesystem_changed_after_approval(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "orion.db"
    source = tmp_path / "music" / "a.flac"
    target = tmp_path / "quarantine" / "a.flac"
    source.parent.mkdir()
    source.write_bytes(b"audio")

    plan = _seed_plan(db_path, source, target)
    target.parent.mkdir()
    source.replace(target)

    filesystem = LocalFilesystemMutator()

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    finding = reconcile_action_plan(
        ReconcileActionPlan(plan.id),
        filesystem,
        FrozenClock(datetime(2026, 8, 3, 2, 0, tzinfo=UTC)),
        factory,
    )
    approval = approve_recovery(
        ApproveRecovery(finding.id, "operator"),
        FrozenClock(datetime(2026, 8, 3, 2, 1, tzinfo=UTC)),
        factory,
    )

    target.replace(source)

    with pytest.raises(ConflictError, match="no longer matches"):
        apply_recovery(
            ApplyRecovery(approval.id, "operator"),
            filesystem,
            FrozenClock(datetime(2026, 8, 3, 2, 2, tzinfo=UTC)),
            factory,
        )
