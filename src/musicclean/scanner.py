from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from musicclean.config import ScannerConfig
from musicclean.database import Database
from musicclean.models import FileRecord

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ScanResult:
    files_seen: int = 0
    files_changed: int = 0
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


def scan_root(
    database: Database,
    root_name: str,
    root: Path,
    config: ScannerConfig,
) -> ScanResult:
    result = ScanResult()
    scan_id = database.start_scan(root_name, root)
    batch: list[FileRecord] = []

    try:
        for record in iter_audio_files(root_name, root, config):
            result.files_seen += 1
            batch.append(record)

            if len(batch) >= config.batch_size:
                result.files_changed += database.upsert_files(batch)
                batch.clear()

        if batch:
            result.files_changed += database.upsert_files(batch)

    except Exception:
        result.errors += 1
        LOGGER.exception("Unhandled scan failure for %s", root)
        raise
    finally:
        database.finish_scan(
            scan_id,
            files_seen=result.files_seen,
            files_changed=result.files_changed,
            errors=result.errors,
        )

    return result
