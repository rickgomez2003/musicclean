from datetime import UTC, datetime
from pathlib import Path

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.domain import AudioFile, EvidenceKind, EvidenceProvenance, EvidenceRecord
from musicclean.orion.shared import ByteSize


def test_evidence_round_trips_with_typed_values(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    audio_file = AudioFile(location="/music/a.flac", size=ByteSize(100))
    provenance = EvidenceProvenance(
        provider="mutagen",
        provider_version="1.0",
        observed_at=datetime(2026, 8, 3, tzinfo=UTC),
    )
    records = (
        EvidenceRecord(audio_file.id, EvidenceKind.TITLE, "Track", provenance),
        EvidenceRecord(audio_file.id, EvidenceKind.SAMPLE_RATE, 96000, provenance),
        EvidenceRecord(audio_file.id, EvidenceKind.DURATION_SECONDS, 123.4, provenance),
        EvidenceRecord(audio_file.id, EvidenceKind.HAS_ARTWORK, True, provenance),
    )

    with SqliteUnitOfWork(db_path) as uow:
        uow.audio_files.save(audio_file)
        uow.evidence.save_many(records)
        uow.commit()

    with SqliteUnitOfWork(db_path) as uow:
        loaded = uow.evidence.list_for_subject(audio_file.id)

    values_by_kind = {record.kind: record.value for record in loaded}

    assert values_by_kind == {
        EvidenceKind.TITLE: "Track",
        EvidenceKind.SAMPLE_RATE: 96000,
        EvidenceKind.DURATION_SECONDS: 123.4,
        EvidenceKind.HAS_ARTWORK: True,
    }
