from datetime import UTC, datetime
from pathlib import Path

import pytest

from musicclean.orion.adapters.filesystem import LocalFilesystemMutator
from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import (
    AuthorizeDecision,
    ConflictError,
    ExecuteQuarantine,
    PlanQuarantine,
    RestoreQuarantine,
    ReviewDecision,
    authorize_decision,
    execute_quarantine,
    plan_quarantine,
    restore_quarantine,
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
    KnowledgeFact,
    KnowledgeKind,
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


def test_quarantine_and_restore_are_reversible(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    source = tmp_path / "music" / "a.flac"
    target = tmp_path / "quarantine" / "a.flac"
    source.parent.mkdir()
    source.write_bytes(b"audio")

    plan = _seed_plan(db_path, source, target)
    filesystem = LocalFilesystemMutator()

    quarantine_clock = FrozenClock(datetime(2026, 8, 3, 2, 0, tzinfo=UTC))
    restore_clock = FrozenClock(datetime(2026, 8, 3, 2, 1, tzinfo=UTC))

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    quarantine = execute_quarantine(
        ExecuteQuarantine(plan.id, "operator"),
        filesystem,
        quarantine_clock,
        factory,
    )
    assert quarantine.kind is ExecutionKind.QUARANTINE
    assert not source.exists()
    assert target.exists()

    restore = restore_quarantine(
        RestoreQuarantine(plan.id, "operator"),
        filesystem,
        restore_clock,
        factory,
    )
    assert restore.kind is ExecutionKind.RESTORE
    assert source.read_bytes() == b"audio"
    assert not target.exists()

    with SqliteUnitOfWork(db_path) as uow:
        executions = uow.executions.list_for_plan(plan.id)
    assert [item.kind for item in executions] == [
        ExecutionKind.QUARANTINE,
        ExecutionKind.RESTORE,
    ]


def test_executor_refuses_existing_quarantine_target(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    source = tmp_path / "music" / "a.flac"
    target = tmp_path / "quarantine" / "a.flac"
    source.parent.mkdir()
    target.parent.mkdir()
    source.write_bytes(b"source")
    target.write_bytes(b"existing")

    plan = _seed_plan(db_path, source, target)

    with pytest.raises(ConflictError, match="target already exists"):
        execute_quarantine(
            ExecuteQuarantine(plan.id, "operator"),
            LocalFilesystemMutator(),
            FrozenClock(datetime(2026, 8, 3, 2, 0, tzinfo=UTC)),
            lambda: SqliteUnitOfWork(db_path),
        )

    assert source.read_bytes() == b"source"
    assert target.read_bytes() == b"existing"
