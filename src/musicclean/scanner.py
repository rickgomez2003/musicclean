from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from musicclean.config import ScannerConfig
from musicclean.database import Database
from musicclean.hashing import hash_file
from musicclean.metadata import read_audio_metadata
from musicclean.models import AnalyzedFile, AudioMetadata, FileRecord

LOGGER = logging.getLogger(__name__)
ProgressCallback = Callable[[int, int, int, Path], None]


@dataclass(slots=True)
class ScanResult:
    files_seen: int = 0
    files_analyzed: int = 0
    files_unchanged: int = 0
    errors: int = 0


def _is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts if part not in {".", ".."})


def iter_audio_files(
    root_name: str,
    root: Path,
    config: ScannerConfig,
) -> Iterator[FileRecord]:
    stack = [root]

    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        path = Path(entry.path)

                        if not config.include_hidden and _is_hidden(path.relative_to(root)):
                            continue

                        if entry.is_dir(follow_symlinks=config.follow_symlinks):
                            stack.append(path)
                            continue

                        if not entry.is_file(follow_symlinks=config.follow_symlinks):
                            continue

                        extension = path.suffix.lower()
                        if extension not in config.extensions:
                            continue

                        stat_result = entry.stat(follow_symlinks=config.follow_symlinks)
                        yield FileRecord(
                            path=path,
                            root_name=root_name,
                            directory=path.parent,
                            filename=path.name,
                            extension=extension,
                            size=int(stat_result.st_size),
                            modified_ns=int(stat_result.st_mtime_ns),
                            inode=int(stat_result.st_ino),
                            device=int(stat_result.st_dev),
                        )
                    except OSError as exc:
                        LOGGER.warning("Unable to inspect %s: %s", entry.path, exc)
        except OSError as exc:
            LOGGER.warning("Unable to scan directory %s: %s", directory, exc)


def _analyze(record: FileRecord, config: ScannerConfig) -> AnalyzedFile:
    metadata = (
        read_audio_metadata(record.path)
        if config.read_metadata
        else AudioMetadata()
    )

    content_hash: str | None = None
    hash_algorithm: str | None = None
    if config.hash_files:
        try:
            content_hash = hash_file(record.path, config.hash_chunk_size)
            hash_algorithm = "blake3"
        except OSError as exc:
            message = f"{type(exc).__name__}: {exc}"
            metadata = AudioMetadata(
                codec=metadata.codec,
                bitrate=metadata.bitrate,
                sample_rate=metadata.sample_rate,
                bits_per_sample=metadata.bits_per_sample,
                channels=metadata.channels,
                duration=metadata.duration,
                title=metadata.title,
                artist=metadata.artist,
                album=metadata.album,
                album_artist=metadata.album_artist,
                track_number=metadata.track_number,
                disc_number=metadata.disc_number,
                date=metadata.date,
                musicbrainz_track_id=metadata.musicbrainz_track_id,
                musicbrainz_album_id=metadata.musicbrainz_album_id,
                musicbrainz_artist_id=metadata.musicbrainz_artist_id,
                has_artwork=metadata.has_artwork,
                error=metadata.error or message,
            )

    return AnalyzedFile(
        file=record,
        metadata=metadata,
        content_hash=content_hash,
        hash_algorithm=hash_algorithm,
    )


def _process_batch(
    database: Database,
    batch: list[FileRecord],
    config: ScannerConfig,
    result: ScanResult,
    progress: ProgressCallback | None,
) -> None:
    database.upsert_inventory(batch)
    existing = database.analysis_state([record.path for record in batch])
    analyzed: list[AnalyzedFile] = []

    for record in batch:
        state = existing.get(str(record.path))
        unchanged = state == (record.size, record.modified_ns)

        if unchanged:
            result.files_unchanged += 1
        else:
            try:
                analyzed.append(_analyze(record, config))
                result.files_analyzed += 1
            except Exception:
                result.errors += 1
                LOGGER.exception("Unable to analyze %s", record.path)

        if progress is not None:
            progress(
                result.files_seen,
                result.files_analyzed,
                result.files_unchanged,
                record.path,
            )

    if analyzed:
        database.save_analysis(analyzed)


def scan_root(
    database: Database,
    root_name: str,
    root: Path,
    config: ScannerConfig,
    progress: ProgressCallback | None = None,
) -> ScanResult:
    result = ScanResult()
    scan_id = database.start_scan(root_name, root)
    batch: list[FileRecord] = []

    try:
        for record in iter_audio_files(root_name, root, config):
            result.files_seen += 1
            batch.append(record)

            if len(batch) >= config.batch_size:
                _process_batch(database, batch, config, result, progress)
                batch.clear()

        if batch:
            _process_batch(database, batch, config, result, progress)

    except Exception:
        result.errors += 1
        LOGGER.exception("Unhandled scan failure for %s", root)
        raise
    finally:
        database.finish_scan(
            scan_id,
            files_seen=result.files_seen,
            files_analyzed=result.files_analyzed,
            files_unchanged=result.files_unchanged,
            errors=result.errors,
        )

    return result
