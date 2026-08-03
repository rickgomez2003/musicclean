from datetime import UTC, datetime
from pathlib import Path

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import CollectMetadataEvidence, collect_metadata_evidence
from musicclean.orion.domain import AudioFile, EvidenceKind
from musicclean.orion.ports import MetadataParser, MetadataSnapshot
from musicclean.orion.shared import ByteSize, FrozenClock


class FakeProvider:
    def read(self, path: Path) -> MetadataSnapshot:
        return MetadataSnapshot(
            title="Track",
            sample_rate=384000,
            bits_per_sample=32,
            parser=MetadataParser.FFPROBE,
            parser_warning="fallback used",
        )


def test_collect_metadata_evidence_persists_provenance(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    audio_file = AudioFile(location="/music/a.wv", size=ByteSize(100))

    with SqliteUnitOfWork(db_path) as uow:
        uow.audio_files.save(audio_file)
        uow.commit()

    records = collect_metadata_evidence(
        CollectMetadataEvidence(
            audio_file_id=audio_file.id,
            path=Path("/music/a.wv"),
            provider_name="legacy-metadata",
            provider_version="0.6.7",
        ),
        FakeProvider(),
        FrozenClock(datetime(2026, 8, 3, tzinfo=UTC)),
        lambda: SqliteUnitOfWork(db_path),
    )

    assert {record.kind for record in records} >= {
        EvidenceKind.TITLE,
        EvidenceKind.SAMPLE_RATE,
        EvidenceKind.BITS_PER_SAMPLE,
    }
    assert all(record.provenance.provider == "legacy-metadata" for record in records)
    assert all(record.provenance.warning == "fallback used" for record in records)

    with SqliteUnitOfWork(db_path) as uow:
        persisted = uow.evidence.list_for_subject(audio_file.id)
    assert len(persisted) == len(records)
