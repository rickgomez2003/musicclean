"""Adapter around MusicClean's proven metadata extraction pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import SupportsFloat, SupportsIndex, SupportsInt

from musicclean.metadata import read_audio_metadata
from musicclean.orion.ports import MetadataParser, MetadataSnapshot


class LegacyMetadataProvider:
    """Expose the existing Mutagen/FFprobe pipeline through the Orion port.

    The existing pipeline remains responsible for parser fallback behavior.
    Orion normalizes its output and records parser provenance where available.
    """

    def read(self, path: Path) -> MetadataSnapshot:
        metadata = read_audio_metadata(path)

        parser_name = str(getattr(metadata, "parser", "") or "").casefold()
        parser = _parser_from_name(parser_name)

        warning = getattr(metadata, "parser_warning", None)
        if warning is None:
            warning = getattr(metadata, "metadata_error", None)

        return MetadataSnapshot(
            title=_optional_str(getattr(metadata, "title", None)),
            artist=_optional_str(getattr(metadata, "artist", None)),
            album=_optional_str(getattr(metadata, "album", None)),
            album_artist=_optional_str(getattr(metadata, "album_artist", None)),
            track_number=_optional_str(getattr(metadata, "track_number", None)),
            disc_number=_optional_str(getattr(metadata, "disc_number", None)),
            codec=_optional_str(getattr(metadata, "codec", None)),
            bitrate=_optional_int(getattr(metadata, "bitrate", None)),
            sample_rate=_optional_int(getattr(metadata, "sample_rate", None)),
            bits_per_sample=_optional_int(getattr(metadata, "bits_per_sample", None)),
            duration_seconds=_optional_float(getattr(metadata, "duration", None)),
            has_artwork=bool(getattr(metadata, "has_artwork", False)),
            musicbrainz_track_id=_optional_str(getattr(metadata, "musicbrainz_track_id", None)),
            musicbrainz_album_id=_optional_str(getattr(metadata, "musicbrainz_album_id", None)),
            parser=parser,
            parser_warning=_optional_str(warning),
        )


def _parser_from_name(value: str) -> MetadataParser:
    if "ffprobe" in value:
        return MetadataParser.FFPROBE
    if "mutagen" in value:
        return MetadataParser.MUTAGEN
    return MetadataParser.UNKNOWN


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _optional_int(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None

    if not isinstance(
        value,
        (str, bytes, bytearray, SupportsInt, SupportsIndex),
    ):
        return None

    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _optional_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    if not isinstance(
        value,
        (str, bytes, bytearray, SupportsFloat, SupportsIndex),
    ):
        return None

    try:
        return float(value)
    except (TypeError, ValueError, OverflowError):
        return None
