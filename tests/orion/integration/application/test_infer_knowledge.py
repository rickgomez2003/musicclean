from datetime import UTC, datetime
from pathlib import Path

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import InferKnowledge, infer_knowledge
from musicclean.orion.domain import (
    AudioFile,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceRecord,
    KnowledgeKind,
)
from musicclean.orion.shared import ByteSize, FrozenClock


def test_infer_knowledge_persists_traceable_facts(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    audio_file = AudioFile(location="/music/a.flac", size=ByteSize(100))
    provenance = EvidenceProvenance(
        provider="metadata",
        observed_at=datetime(2026, 8, 3, tzinfo=UTC),
    )
    evidence = (
        EvidenceRecord(audio_file.id, EvidenceKind.TITLE, "Track", provenance),
        EvidenceRecord(audio_file.id, EvidenceKind.ARTIST, "Artist", provenance),
        EvidenceRecord(audio_file.id, EvidenceKind.ALBUM, "Album", provenance),
        EvidenceRecord(audio_file.id, EvidenceKind.SAMPLE_RATE, 96000, provenance),
        EvidenceRecord(audio_file.id, EvidenceKind.BITS_PER_SAMPLE, 24, provenance),
    )

    with SqliteUnitOfWork(db_path) as uow:
        uow.audio_files.save(audio_file)
        uow.evidence.save_many(evidence)
        uow.commit()

    facts = infer_knowledge(
        InferKnowledge(audio_file.id),
        FrozenClock(datetime(2026, 8, 3, 1, 0, tzinfo=UTC)),
        lambda: SqliteUnitOfWork(db_path),
    )

    facts_by_kind = {fact.kind: fact for fact in facts}
    assert facts_by_kind[KnowledgeKind.CORE_METADATA_COMPLETE].value is True
    assert facts_by_kind[KnowledgeKind.HIGH_RESOLUTION_FORMAT].value is True
    assert all(fact.evidence_ids for fact in facts)

    with SqliteUnitOfWork(db_path) as uow:
        persisted = uow.knowledge.list_for_subject(audio_file.id)

    assert len(persisted) == 2
