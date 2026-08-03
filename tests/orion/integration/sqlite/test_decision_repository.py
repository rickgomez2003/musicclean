from datetime import UTC, datetime
from pathlib import Path

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.domain import (
    AudioFile,
    Decision,
    DecisionAction,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceRecord,
    KnowledgeFact,
    KnowledgeKind,
)
from musicclean.orion.shared import ByteSize, Confidence


def test_decision_round_trips_with_knowledge_links(tmp_path: Path) -> None:
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
    knowledge = KnowledgeFact(
        subject_id=audio_file.id,
        kind=KnowledgeKind.CORE_METADATA_COMPLETE,
        value=True,
        confidence=Confidence(1.0),
        evidence_ids=(evidence.id,),
        rule_id="metadata.core-complete",
        rule_version="1",
        inferred_at=datetime(2026, 8, 3, tzinfo=UTC),
    )
    decision = Decision(
        subject_id=audio_file.id,
        action=DecisionAction.KEEP,
        confidence=Confidence(1.0),
        rationale="Core metadata is complete.",
        knowledge_ids=(knowledge.id,),
        rule_id="decision.metadata-repair",
        rule_version="1",
        decided_at=datetime(2026, 8, 3, tzinfo=UTC),
        risk="No destructive action is proposed.",
    )

    with SqliteUnitOfWork(db_path) as uow:
        uow.audio_files.save(audio_file)
        uow.evidence.save(evidence)
        uow.knowledge.save(knowledge)
        uow.decisions.save(decision)
        uow.commit()

    with SqliteUnitOfWork(db_path) as uow:
        loaded = uow.decisions.list_for_subject(audio_file.id)

    assert loaded == (decision,)
