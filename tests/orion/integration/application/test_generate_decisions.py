from datetime import UTC, datetime
from pathlib import Path

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import GenerateDecisions, generate_decisions
from musicclean.orion.domain import (
    AudioFile,
    DecisionAction,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceRecord,
    KnowledgeFact,
    KnowledgeKind,
)
from musicclean.orion.shared import ByteSize, Confidence, FrozenClock


def test_generate_decisions_persists_explainable_recommendations(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "orion.db"
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
    knowledge = (
        KnowledgeFact(
            subject_id=audio_file.id,
            kind=KnowledgeKind.CORE_METADATA_COMPLETE,
            value=False,
            confidence=Confidence(1.0),
            evidence_ids=(evidence.id,),
            rule_id="metadata.core-complete",
            rule_version="1",
            inferred_at=datetime(2026, 8, 3, tzinfo=UTC),
        ),
        KnowledgeFact(
            subject_id=audio_file.id,
            kind=KnowledgeKind.HIGH_RESOLUTION_FORMAT,
            value=True,
            confidence=Confidence(1.0),
            evidence_ids=(evidence.id,),
            rule_id="audio.high-resolution-format",
            rule_version="1",
            inferred_at=datetime(2026, 8, 3, tzinfo=UTC),
        ),
    )

    with SqliteUnitOfWork(db_path) as uow:
        uow.audio_files.save(audio_file)
        uow.evidence.save(evidence)
        uow.knowledge.save_many(knowledge)
        uow.commit()

    decisions = generate_decisions(
        GenerateDecisions(audio_file.id),
        FrozenClock(datetime(2026, 8, 3, 1, 0, tzinfo=UTC)),
        lambda: SqliteUnitOfWork(db_path),
    )

    assert {decision.action for decision in decisions} == {
        DecisionAction.REPAIR_METADATA,
        DecisionAction.REVIEW,
    }
    assert all(decision.knowledge_ids for decision in decisions)

    with SqliteUnitOfWork(db_path) as uow:
        persisted = uow.decisions.list_for_subject(audio_file.id)

    assert len(persisted) == 2
