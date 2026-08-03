from datetime import UTC, datetime
from pathlib import Path

from musicclean.orion.adapters.filesystem import LocalFilesystemMutator
from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import (
    AuthorizeDecision,
    PlanQuarantine,
    ReconcileActionPlan,
    ReviewDecision,
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
    KnowledgeFact,
    KnowledgeKind,
    ReconciliationAction,
    ReconciliationStatus,
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


def test_reconcile_detects_missing_quarantine_audit(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    source = tmp_path / "music" / "a.flac"
    target = tmp_path / "quarantine" / "a.flac"
    source.parent.mkdir()
    source.write_bytes(b"audio")

    plan = _seed_plan(db_path, source, target)

    target.parent.mkdir()
    source.replace(target)

    def factory() -> SqliteUnitOfWork:
        return SqliteUnitOfWork(db_path)

    finding = reconcile_action_plan(
        ReconcileActionPlan(plan.id),
        LocalFilesystemMutator(),
        FrozenClock(datetime(2026, 8, 3, 2, 0, tzinfo=UTC)),
        factory,
    )

    assert finding.status is ReconciliationStatus.AUDIT_MISSING_AFTER_QUARANTINE
    assert finding.proposed_action is ReconciliationAction.RECOVER_QUARANTINE_AUDIT

    with SqliteUnitOfWork(db_path) as uow:
        persisted = uow.reconciliations.list_for_plan(plan.id)

    assert persisted == (finding,)
