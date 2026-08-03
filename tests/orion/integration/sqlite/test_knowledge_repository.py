from datetime import UTC, datetime
from pathlib import Path

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.domain import (
    AudioFile,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceRecord,
    KnowledgeFact,
    KnowledgeKind,
)
from musicclean.orion.shared import ByteSize, Confidence


def test_knowledge_round_trips_with_evidence_links(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    audio_file = AudioFile(location="/music/a.flac", size=ByteSize(100))
    evidence = EvidenceRecord(
        subject_id=audio_file.id,
        kind=EvidenceKind.SAMPLE_RATE,
        value=96000,
        provenance=EvidenceProvenance(
            provider="test",
            observed_at=datetime(2026, 8, 3, tzinfo=UTC),
        ),
    )
    fact = KnowledgeFact(
        subject_id=audio_file.id,
        kind=KnowledgeKind.HIGH_RESOLUTION_FORMAT,
        value=True,
        confidence=Confidence(1.0),
        evidence_ids=(evidence.id,),
        rule_id="audio.high-resolution-format",
        rule_version="1",
        inferred_at=datetime(2026, 8, 3, tzinfo=UTC),
    )

    with SqliteUnitOfWork(db_path) as uow:
        uow.audio_files.save(audio_file)
        uow.evidence.save(evidence)
        uow.knowledge.save(fact)
        uow.commit()

    with SqliteUnitOfWork(db_path) as uow:
        loaded = uow.knowledge.list_for_subject(audio_file.id)

    assert loaded == (fact,)
