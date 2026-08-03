"""Evidence domain model with explicit provenance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from musicclean.orion.domain._validation import optional_text, require_text
from musicclean.orion.shared import EntityId

EvidenceValue = str | int | float | bool


class EvidenceKind(StrEnum):
    """Normalized observation kinds currently emitted by Orion."""

    TITLE = "title"
    ARTIST = "artist"
    ALBUM = "album"
    ALBUM_ARTIST = "album_artist"
    TRACK_NUMBER = "track_number"
    DISC_NUMBER = "disc_number"
    CODEC = "codec"
    BITRATE = "bitrate"
    SAMPLE_RATE = "sample_rate"
    BITS_PER_SAMPLE = "bits_per_sample"
    DURATION_SECONDS = "duration_seconds"
    HAS_ARTWORK = "has_artwork"
    MUSICBRAINZ_TRACK_ID = "musicbrainz_track_id"
    MUSICBRAINZ_ALBUM_ID = "musicbrainz_album_id"


@dataclass(frozen=True, slots=True)
class EvidenceProvenance:
    """Where, when, and how an observation was produced."""

    provider: str
    observed_at: datetime
    provider_version: str | None = None
    warning: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider", require_text(self.provider, "provider"))
        object.__setattr__(self, "provider_version", optional_text(self.provider_version))
        object.__setattr__(self, "warning", optional_text(self.warning))
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        object.__setattr__(self, "observed_at", self.observed_at.astimezone(UTC))


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """One immutable observation about a domain subject."""

    subject_id: EntityId
    kind: EvidenceKind
    value: EvidenceValue
    provenance: EvidenceProvenance
    id: EntityId = field(default_factory=EntityId.new)
