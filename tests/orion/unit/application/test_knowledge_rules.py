from datetime import UTC, datetime

from musicclean.orion.application import (
    CoreMetadataCompleteRule,
    HighResolutionFormatRule,
    latest_evidence_by_kind,
)
from musicclean.orion.domain import (
    EvidenceKind,
    EvidenceProvenance,
    EvidenceRecord,
    KnowledgeKind,
)
from musicclean.orion.shared import EntityId


def _record(
    subject_id: EntityId,
    kind: EvidenceKind,
    value: str | int | float | bool,
    minute: int = 0,
) -> EvidenceRecord:
    return EvidenceRecord(
        subject_id=subject_id,
        kind=kind,
        value=value,
        provenance=EvidenceProvenance(
            provider="test",
            observed_at=datetime(2026, 8, 3, 12, minute, tzinfo=UTC),
        ),
    )


def test_latest_evidence_by_kind_prefers_newer_observation() -> None:
    subject = EntityId.new()
    older = _record(subject, EvidenceKind.TITLE, "Old", 0)
    newer = _record(subject, EvidenceKind.TITLE, "New", 1)

    latest = latest_evidence_by_kind((older, newer))

    assert latest[EvidenceKind.TITLE] == newer


def test_core_metadata_complete_rule_true_when_required_fields_exist() -> None:
    subject = EntityId.new()
    evidence = (
        _record(subject, EvidenceKind.TITLE, "Track"),
        _record(subject, EvidenceKind.ARTIST, "Artist"),
        _record(subject, EvidenceKind.ALBUM, "Album"),
    )

    fact = CoreMetadataCompleteRule().infer(
        subject,
        evidence,
        datetime.now(UTC),
    )

    assert fact is not None
    assert fact.kind is KnowledgeKind.CORE_METADATA_COMPLETE
    assert fact.value is True
    assert len(fact.evidence_ids) == 3


def test_core_metadata_complete_rule_false_when_some_required_fields_missing() -> None:
    subject = EntityId.new()
    evidence = (_record(subject, EvidenceKind.TITLE, "Track"),)

    fact = CoreMetadataCompleteRule().infer(
        subject,
        evidence,
        datetime.now(UTC),
    )

    assert fact is not None
    assert fact.value is False


def test_high_resolution_rule_is_technical_classification() -> None:
    subject = EntityId.new()
    evidence = (
        _record(subject, EvidenceKind.SAMPLE_RATE, 96000),
        _record(subject, EvidenceKind.BITS_PER_SAMPLE, 24),
    )

    fact = HighResolutionFormatRule().infer(
        subject,
        evidence,
        datetime.now(UTC),
    )

    assert fact is not None
    assert fact.kind is KnowledgeKind.HIGH_RESOLUTION_FORMAT
    assert fact.value is True


def test_high_resolution_rule_false_for_cd_format() -> None:
    subject = EntityId.new()
    evidence = (
        _record(subject, EvidenceKind.SAMPLE_RATE, 44100),
        _record(subject, EvidenceKind.BITS_PER_SAMPLE, 16),
    )

    fact = HighResolutionFormatRule().infer(
        subject,
        evidence,
        datetime.now(UTC),
    )

    assert fact is not None
    assert fact.value is False
