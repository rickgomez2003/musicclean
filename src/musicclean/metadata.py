from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from mutagen import File as MutagenFile
from mutagen.apev2 import APENoHeaderError, APEv2

from musicclean.models import AudioMetadata


def _clean_text(value: object) -> str | None:
    try:
        text = str(value).replace("\x00", "").strip()
    except Exception:
        return None
    return text or None


def _first(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").replace("\x00", "").strip() or None
    if isinstance(value, str):
        return value.replace("\x00", "").strip() or None

    for attribute in ("text", "value"):
        try:
            nested = getattr(value, attribute, None)
        except Exception:
            nested = None
        if nested is not None and nested is not value:
            result = _first(nested)
            if result:
                return result

    if isinstance(value, Mapping):
        for nested in value.values():
            result = _first(nested)
            if result:
                return result
        return None

    if isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            result = _first(item)
            if result:
                return result
        return None

    return _clean_text(value)


def _normalized_tags(tags: Any) -> dict[str, Any]:
    if tags is None:
        return {}
    try:
        items = tags.items()
    except Exception:
        return {}

    normalized: dict[str, Any] = {}
    try:
        for key, value in items:
            normalized[str(key).casefold()] = value
    except Exception:
        return normalized
    return normalized


def _tag(tags: Any, *keys: str) -> str | None:
    normalized = _normalized_tags(tags)
    for key in keys:
        result = _first(normalized.get(key.casefold()))
        if result:
            return result
    return None


def _has_artwork_from_tags(tags: Any) -> bool:
    keys = set(_normalized_tags(tags))
    return any(
        key.startswith("apic")
        or key.startswith("cover art")
        or key in {"covr", "coverart", "metadata_block_picture"}
        for key in keys
    )


def _has_artwork(audio: Any) -> bool:
    try:
        if getattr(audio, "pictures", None):
            return True
    except Exception:
        pass
    return _has_artwork_from_tags(getattr(audio, "tags", None))


def _safe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError, OverflowError):
        return None


def _safe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError, OverflowError):
        return None


def _metadata_from_parts(
    *, codec: str | None, info: Any, tags: Any, artwork: bool
) -> AudioMetadata:
    return AudioMetadata(
        codec=codec,
        bitrate=_safe_int(getattr(info, "bitrate", None)),
        sample_rate=_safe_int(getattr(info, "sample_rate", None)),
        bits_per_sample=_safe_int(getattr(info, "bits_per_sample", None)),
        channels=_safe_int(getattr(info, "channels", None)),
        duration=_safe_float(getattr(info, "length", None)),
        title=_tag(tags, "title", "TIT2", "©nam"),
        artist=_tag(tags, "artist", "TPE1", "©ART"),
        album=_tag(tags, "album", "TALB", "©alb"),
        album_artist=_tag(tags, "albumartist", "album artist", "TPE2", "aART"),
        track_number=_tag(tags, "tracknumber", "track", "TRCK", "trkn"),
        disc_number=_tag(tags, "discnumber", "disc", "TPOS", "disk"),
        date=_tag(tags, "date", "year", "TDRC", "©day"),
        musicbrainz_track_id=_tag(
            tags,
            "musicbrainz_trackid",
            "musicbrainz track id",
            "UFID:http://musicbrainz.org",
        ),
        musicbrainz_album_id=_tag(tags, "musicbrainz_albumid", "musicbrainz album id"),
        musicbrainz_artist_id=_tag(tags, "musicbrainz_artistid", "musicbrainz artist id"),
        has_artwork=artwork,
    )


def _read_apev2_tags(path: Path) -> Any:
    try:
        return APEv2(path)  # type: ignore[no-untyped-call]
    except (APENoHeaderError, OSError, ValueError):
        return None


def _ffprobe(path: Path) -> dict[str, Any]:
    executable = shutil.which("ffprobe")
    if executable is None:
        raise RuntimeError("ffprobe was not found in PATH")

    command = [
        executable,
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit code {completed.returncode}"
        raise RuntimeError(f"ffprobe failed: {detail}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("ffprobe returned an unexpected response")
    return payload


def _ffprobe_metadata(path: Path) -> tuple[AudioMetadata, dict[str, Any]]:
    payload = _ffprobe(path)
    streams_value = payload.get("streams")
    stream: dict[str, Any] = {}
    if isinstance(streams_value, list):
        stream = next(
            (
                item
                for item in streams_value
                if isinstance(item, dict) and item.get("codec_type") == "audio"
            ),
            {},
        )
    format_value = payload.get("format")
    format_data: dict[str, Any] = format_value if isinstance(format_value, dict) else {}

    ff_tags: dict[str, Any] = {}
    for source in (format_data.get("tags"), stream.get("tags")):
        if isinstance(source, dict):
            ff_tags.update(source)

    ape_tags = _read_apev2_tags(path) if path.suffix.casefold() == ".wv" else None
    tags: Any = ape_tags if ape_tags is not None else ff_tags

    bits = _safe_int(stream.get("bits_per_raw_sample")) or _safe_int(stream.get("bits_per_sample"))
    codec = _clean_text(stream.get("codec_long_name")) or _clean_text(stream.get("codec_name"))
    duration = _safe_float(stream.get("duration")) or _safe_float(format_data.get("duration"))
    bitrate = _safe_int(stream.get("bit_rate")) or _safe_int(format_data.get("bit_rate"))

    metadata = AudioMetadata(
        codec=codec,
        bitrate=bitrate,
        sample_rate=_safe_int(stream.get("sample_rate")),
        bits_per_sample=bits,
        channels=_safe_int(stream.get("channels")),
        duration=duration,
        title=_tag(tags, "title"),
        artist=_tag(tags, "artist"),
        album=_tag(tags, "album"),
        album_artist=_tag(tags, "albumartist", "album artist"),
        track_number=_tag(tags, "tracknumber", "track"),
        disc_number=_tag(tags, "discnumber", "disc"),
        date=_tag(tags, "date", "year"),
        musicbrainz_track_id=_tag(tags, "musicbrainz_trackid", "musicbrainz track id"),
        musicbrainz_album_id=_tag(tags, "musicbrainz_albumid", "musicbrainz album id"),
        musicbrainz_artist_id=_tag(tags, "musicbrainz_artistid", "musicbrainz artist id"),
        has_artwork=_has_artwork_from_tags(tags),
    )
    diagnostic = {
        "parser": "ffprobe" + (" + mutagen.apev2.APEv2" if ape_tags is not None else ""),
        "tag_type": type(tags).__name__ if tags is not None else None,
        "tag_count": len(_normalized_tags(tags)),
        "tag_keys": sorted(_normalized_tags(tags)),
    }
    return metadata, diagnostic


def read_audio_metadata(path: Path) -> AudioMetadata:
    """Extract technical and common tag metadata without modifying the file."""
    try:
        audio = MutagenFile(path, easy=False)
        if audio is None:
            return AudioMetadata(error="Unsupported or unrecognized audio file")
        return _metadata_from_parts(
            codec=type(audio).__name__,
            info=getattr(audio, "info", None),
            tags=getattr(audio, "tags", None),
            artwork=_has_artwork(audio),
        )
    except Exception as mutagen_exc:
        try:
            metadata, _ = _ffprobe_metadata(path)
            return metadata
        except Exception as ffprobe_exc:
            return AudioMetadata(
                error=(
                    f"Mutagen {type(mutagen_exc).__name__}: {mutagen_exc}; "
                    f"fallback {type(ffprobe_exc).__name__}: {ffprobe_exc}"
                )
            )


def inspect_audio_file(path: Path) -> dict[str, object]:
    """Return parser diagnostics and normalized metadata for one audio file."""
    result: dict[str, object] = {
        "path": str(path),
        "exists": path.is_file(),
        "size": path.stat().st_size if path.is_file() else None,
    }
    if not path.is_file():
        result["error"] = "File does not exist or is not a regular file"
        return result

    try:
        audio = MutagenFile(path, easy=False)
        if audio is None:
            result["error"] = "Unsupported or unrecognized audio file"
            return result
        tags = getattr(audio, "tags", None)
        metadata = _metadata_from_parts(
            codec=type(audio).__name__,
            info=getattr(audio, "info", None),
            tags=tags,
            artwork=_has_artwork(audio),
        )
        normalized = _normalized_tags(tags)
        result.update(
            {
                "parser": f"{type(audio).__module__}.{type(audio).__name__}",
                "tag_type": type(tags).__name__ if tags is not None else None,
                "tag_count": len(normalized),
                "tag_keys": sorted(normalized),
                "metadata": asdict(metadata),
            }
        )
    except Exception as mutagen_exc:
        try:
            metadata, fallback = _ffprobe_metadata(path)
            result.update(fallback)
            result["metadata"] = asdict(metadata)
            result["warning"] = f"Mutagen failed: {type(mutagen_exc).__name__}: {mutagen_exc}"
        except Exception as ffprobe_exc:
            result["error"] = (
                f"Mutagen {type(mutagen_exc).__name__}: {mutagen_exc}; "
                f"fallback {type(ffprobe_exc).__name__}: {ffprobe_exc}"
            )
    return result
