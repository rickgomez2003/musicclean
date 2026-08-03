from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LOSSLESS_EXTENSIONS = {".flac", ".wv", ".wav", ".aiff", ".aif", ".alac"}


@dataclass(frozen=True, slots=True)
class AlbumTrack:
    path: Path
    directory: Path
    artist: str | None
    album_artist: str | None
    album: str
    title: str | None
    track_number: str | None
    extension: str
    sample_rate: int | None
    bits_per_sample: int | None
    bitrate: int | None
    has_artwork: bool
    musicbrainz_track_id: str | None
    musicbrainz_album_id: str | None
    metadata_error: str | None


@dataclass(frozen=True, slots=True)
class AlbumEdition:
    artist: str
    album: str
    directory: Path
    tracks: tuple[AlbumTrack, ...]
    score: int
    stars: str
    recommendation: str
    reasons: tuple[str, ...]

    @property
    def track_count(self) -> int:
        return len(self.tracks)


def _clean(value: str | None, fallback: str) -> str:
    value = value.strip() if value else ""
    return value or fallback


def _score(tracks: tuple[AlbumTrack, ...]) -> tuple[int, tuple[str, ...]]:
    score = 0
    reasons: list[str] = []
    count = max(1, len(tracks))
    lossless = sum(track.extension.casefold() in LOSSLESS_EXTENSIONS for track in tracks)
    metadata_complete = sum(
        bool(track.title and (track.artist or track.album_artist)) for track in tracks
    )
    artwork = sum(track.has_artwork for track in tracks)
    mb_tracks = sum(bool(track.musicbrainz_track_id) for track in tracks)
    errors = sum(bool(track.metadata_error) for track in tracks)
    max_rate = max((track.sample_rate or 0 for track in tracks), default=0)
    max_depth = max((track.bits_per_sample or 0 for track in tracks), default=0)

    lossless_ratio = lossless / count
    metadata_ratio = metadata_complete / count
    artwork_ratio = artwork / count
    mb_ratio = mb_tracks / count

    score += round(lossless_ratio * 25)
    score += round(metadata_ratio * 25)
    score += round(artwork_ratio * 10)
    score += round(mb_ratio * 15)
    score += 10 if max_rate >= 96000 else 6 if max_rate >= 48000 else 3
    score += 10 if max_depth >= 24 else 5 if max_depth >= 16 else 0
    score += min(5, count)
    score -= min(25, errors * 5)
    score = max(0, min(100, score))

    reasons.append(f"{lossless}/{count} lossless tracks")
    reasons.append(f"{metadata_complete}/{count} tracks with core metadata")
    if artwork:
        reasons.append(f"artwork on {artwork}/{count} tracks")
    if mb_tracks:
        reasons.append(f"MusicBrainz IDs on {mb_tracks}/{count} tracks")
    if max_rate:
        reasons.append(f"up to {max_rate / 1000:g} kHz")
    if max_depth:
        reasons.append(f"up to {max_depth}-bit")
    if errors:
        reasons.append(f"{errors} metadata errors")
    return score, tuple(reasons)


def _rating(score: int) -> tuple[str, str]:
    stars = max(1, min(5, (score + 19) // 20))
    if score >= 80:
        recommendation = "Keep"
    elif score >= 65:
        recommendation = "Archive"
    elif score >= 45:
        recommendation = "Review"
    else:
        recommendation = "Cleanup candidate"
    return "★" * stars + "☆" * (5 - stars), recommendation


def build_album_editions(rows: list[dict[str, Any]]) -> list[AlbumEdition]:
    grouped: dict[tuple[str, str, Path], list[AlbumTrack]] = defaultdict(list)
    for row in rows:
        album = _clean(row.get("album"), "Unknown Album")
        artist = _clean(row.get("album_artist") or row.get("artist"), "Unknown Artist")
        path = Path(str(row["path"]))
        directory = Path(str(row.get("directory") or path.parent))
        track = AlbumTrack(
            path=path,
            directory=directory,
            artist=row.get("artist"),
            album_artist=row.get("album_artist"),
            album=album,
            title=row.get("title"),
            track_number=row.get("track_number"),
            extension=str(row.get("extension") or path.suffix),
            sample_rate=row.get("sample_rate"),
            bits_per_sample=row.get("bits_per_sample"),
            bitrate=row.get("bitrate"),
            has_artwork=bool(row.get("has_artwork")),
            musicbrainz_track_id=row.get("musicbrainz_track_id"),
            musicbrainz_album_id=row.get("musicbrainz_album_id"),
            metadata_error=row.get("metadata_error"),
        )
        grouped[(artist.casefold(), album.casefold(), directory)].append(track)

    editions: list[AlbumEdition] = []
    for (_, _, directory), items in grouped.items():
        tracks = tuple(sorted(items, key=lambda item: (item.track_number or "", item.path.name)))
        score, reasons = _score(tracks)
        stars, recommendation = _rating(score)
        editions.append(
            AlbumEdition(
                artist=_clean(tracks[0].album_artist or tracks[0].artist, "Unknown Artist"),
                album=tracks[0].album,
                directory=directory,
                tracks=tracks,
                score=score,
                stars=stars,
                recommendation=recommendation,
                reasons=reasons,
            )
        )
    return sorted(
        editions,
        key=lambda item: (-item.score, item.artist.casefold(), item.album.casefold()),
    )
