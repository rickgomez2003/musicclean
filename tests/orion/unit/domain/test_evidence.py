from datetime import UTC, datetime, timedelta, timezone

from musicclean.orion.domain import EvidenceKind, EvidenceProvenance, EvidenceRecord
from musicclean.orion.shared import EntityId


def test_provenance_normalizes_to_utc() -> None:
    source = datetime(2026, 8, 3, 10, 0, tzinfo=timezone(timedelta(hours=-4)))
    provenance = EvidenceProvenance(provider="mutagen", observed_at=source)
    assert provenance.observed_at == datetime(2026, 8, 3, 14, 0, tzinfo=UTC)


def test_evidence_record_keeps_subject_kind_value_and_provenance() -> None:
    provenance = EvidenceProvenance(provider="ffprobe", observed_at=datetime.now(UTC))
    record = EvidenceRecord(
        subject_id=EntityId.new(),
        kind=EvidenceKind.SAMPLE_RATE,
        value=384000,
        provenance=provenance,
    )
    assert record.kind is EvidenceKind.SAMPLE_RATE
    assert record.value == 384000
    assert record.provenance.provider == "ffprobe"
