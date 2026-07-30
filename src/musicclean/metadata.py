from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from mutagen import File as MutagenFile

from musicclean.models import AudioMetadata


def _first(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip() or None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, Sequence):
        for item in value:
            result = _first(item)
            if result:
                return result
        return None
    text = str(value).strip()
    return text or None


def _tag(tags: Mapping[str, Any] | None, *keys: str) -> str | None:
    if tags is None:
        return None

    normalized = {str(key).lower(): value for key, value in tags.items()}
    for key in keys:
        value = normalized.get(key.lower())
        result = _first(value)
        if result:
            return result
    return None


def _has_artwork(audio: Any) -> bool:
    pictures = getattr(audio, "pictures", None)
    if pictures:
        return True

    tags = getattr(audio, "tags", None)
    if tags is None:
        return False

    try:
        keys = [str(key).lower() for key in tags]
    except AttributeError:
        return False

    return any(
        key.startswith("apic")
        or key in {"covr", "coverart", "metadata_block_picture"}
        for key in keys
    )


def read_audio_metadata(path: Path) -> AudioMetadata:
    """Extract technical and common tag metadata without modifying the file."""
    try:
        audio = MutagenFile(path, easy=False)
        if audio is None:
            return AudioMetadata(error="Unsupported or unrecognized audio file")

        info = getattr(audio, "info", None)
        tags = getattr(audio, "tags", None)

        codec = type(audio).__name__
        bitrate = getattr(info, "bitrate", None)
        sample_rate = getattr(info, "sample_rate", None)
        bits_per_sample = getattr(info, "bits_per_sample", None)
        channels = getattr(info, "channels", None)
        duration = getattr(info, "length", None)

        return AudioMetadata(
            codec=codec,
            bitrate=int(bitrate) if bitrate is not None else None,
            sample_rate=int(sample_rate) if sample_rate is not None else None,
            bits_per_sample=int(bits_per_sample) if bits_per_sample is not None else None,
            channels=int(channels) if channels is not None else None,
            duration=float(duration) if duration is not None else None,
            title=_tag(tags, "title", "TIT2", "\xa9nam"),
            artist=_tag(tags, "artist", "TPE1", "\xa9ART"),
            album=_tag(tags, "album", "TALB", "\xa9alb"),
            album_artist=_tag(
                tags,
                "albumartist",
                "album artist",
                "TPE2",
                "aART",
            ),
            track_number=_tag(tags, "tracknumber", "TRCK", "trkn"),
            disc_number=_tag(tags, "discnumber", "TPOS", "disk"),
            date=_tag(tags, "date", "year", "TDRC", "\xa9day"),
            musicbrainz_track_id=_tag(
                tags,
                "musicbrainz_trackid",
                "musicbrainz track id",
                "UFID:http://musicbrainz.org",
            ),
            musicbrainz_album_id=_tag(
                tags,
                "musicbrainz_albumid",
                "musicbrainz album id",
            ),
            musicbrainz_artist_id=_tag(
                tags,
                "musicbrainz_artistid",
                "musicbrainz artist id",
            ),
            has_artwork=_has_artwork(audio),
        )
    except Exception as exc:
        return AudioMetadata(error=f"{type(exc).__name__}: {exc}")
