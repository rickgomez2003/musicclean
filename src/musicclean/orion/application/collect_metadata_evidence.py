"""Convert normalized metadata into persistent Evidence records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from musicclean.orion.application.errors import NotFoundError
from musicclean.orion.domain import (
    EvidenceKind,
    EvidenceProvenance,
    EvidenceRecord,
    EvidenceValue,
)
from musicclean.orion.ports import MetadataProvider, MetadataSnapshot, UnitOfWorkFactory
from musicclean.orion.shared import Clock, EntityId


@dataclass(frozen=True, slots=True)
class CollectMetadataEvidence:
    audio_file_id: EntityId
    path: Path
    provider_name: str
    provider_version: str | None = None


def collect_metadata_evidence(
    command: CollectMetadataEvidence,
    provider: MetadataProvider,
    clock: Clock,
    uow_factory: UnitOfWorkFactory,
) -> tuple[EvidenceRecord, ...]:
    """Read metadata, persist normalized observations, and return them."""
    snapshot = provider.read(command.path)

    with uow_factory() as uow:
        if uow.audio_files.get(command.audio_file_id) is None:
            raise NotFoundError(f"audio file not found: {command.audio_file_id}")

        provenance = EvidenceProvenance(
            provider=command.provider_name,
            provider_version=command.provider_version,
            observed_at=clock.now(),
            warning=snapshot.parser_warning,
        )
        records = _snapshot_to_evidence(command.audio_file_id, snapshot, provenance)
        uow.evidence.save_many(records)
        uow.commit()
        return records


def _snapshot_to_evidence(
    subject_id: EntityId,
    snapshot: MetadataSnapshot,
    provenance: EvidenceProvenance,
) -> tuple[EvidenceRecord, ...]:
    observations: tuple[tuple[EvidenceKind, EvidenceValue | None], ...] = (
        (EvidenceKind.TITLE, snapshot.title),
        (EvidenceKind.ARTIST, snapshot.artist),
        (EvidenceKind.ALBUM, snapshot.album),
        (EvidenceKind.ALBUM_ARTIST, snapshot.album_artist),
        (EvidenceKind.TRACK_NUMBER, snapshot.track_number),
        (EvidenceKind.DISC_NUMBER, snapshot.disc_number),
        (EvidenceKind.CODEC, snapshot.codec),
        (EvidenceKind.BITRATE, snapshot.bitrate),
        (EvidenceKind.SAMPLE_RATE, snapshot.sample_rate),
        (EvidenceKind.BITS_PER_SAMPLE, snapshot.bits_per_sample),
        (EvidenceKind.DURATION_SECONDS, snapshot.duration_seconds),
        (EvidenceKind.HAS_ARTWORK, snapshot.has_artwork),
        (EvidenceKind.MUSICBRAINZ_TRACK_ID, snapshot.musicbrainz_track_id),
        (EvidenceKind.MUSICBRAINZ_ALBUM_ID, snapshot.musicbrainz_album_id),
    )
    return tuple(
        EvidenceRecord(
            subject_id=subject_id,
            kind=kind,
            value=value,
            provenance=provenance,
        )
        for kind, value in observations
        if value is not None
    )
