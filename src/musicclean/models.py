from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileRecord:
    path: Path
    root_name: str
    directory: Path
    filename: str
    extension: str
    size: int
    modified_ns: int
    inode: int
    device: int


@dataclass(frozen=True, slots=True)
class AudioMetadata:
    codec: str | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    bits_per_sample: int | None = None
    channels: int | None = None
    duration: float | None = None
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    album_artist: str | None = None
    track_number: str | None = None
    disc_number: str | None = None
    date: str | None = None
    musicbrainz_track_id: str | None = None
    musicbrainz_album_id: str | None = None
    musicbrainz_artist_id: str | None = None
    has_artwork: bool = False
    error: str | None = None


@dataclass(frozen=True, slots=True)
class AnalyzedFile:
    file: FileRecord
    metadata: AudioMetadata
    content_hash: str | None
    hash_algorithm: str | None
