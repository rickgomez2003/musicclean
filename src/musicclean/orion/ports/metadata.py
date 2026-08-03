"""Metadata provider contracts and normalized parser output."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol


class MetadataParser(StrEnum):
    """Parser/provider that supplied the normalized metadata result."""

    MUTAGEN = "mutagen"
    FFPROBE = "ffprobe"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class MetadataSnapshot:
    """Normalized metadata observation returned by a MetadataProvider."""

    title: str | None = None
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None
    track_number: str | None = None
    disc_number: str | None = None
    codec: str | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    bits_per_sample: int | None = None
    duration_seconds: float | None = None
    has_artwork: bool = False
    musicbrainz_track_id: str | None = None
    musicbrainz_album_id: str | None = None
    parser: MetadataParser = MetadataParser.UNKNOWN
    parser_warning: str | None = None


class MetadataProvider(Protocol):
    """Port for reading normalized metadata from an audio file."""

    def read(self, path: Path) -> MetadataSnapshot: ...
