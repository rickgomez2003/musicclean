from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Sequence
from pathlib import Path

from musicclean.models import AnalyzedFile, FileRecord

SCHEMA_VERSION = 2

BASE_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    root_name TEXT NOT NULL,
    directory TEXT NOT NULL,
    filename TEXT NOT NULL,
    extension TEXT NOT NULL,
    size INTEGER NOT NULL,
    modified_ns INTEGER NOT NULL,
    inode INTEGER NOT NULL,
    device INTEGER NOT NULL,
    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_files_size ON files(size);
CREATE INDEX IF NOT EXISTS idx_files_extension ON files(extension);
CREATE INDEX IF NOT EXISTS idx_files_root_name ON files(root_name);
CREATE INDEX IF NOT EXISTS idx_files_modified_ns ON files(modified_ns);

CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    root_name TEXT NOT NULL,
    root_path TEXT NOT NULL,
    files_seen INTEGER NOT NULL DEFAULT 0,
    files_analyzed INTEGER NOT NULL DEFAULT 0,
    files_unchanged INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0
);
"""

FILE_COLUMNS: dict[str, str] = {
    "content_hash": "TEXT",
    "hash_algorithm": "TEXT",
    "codec": "TEXT",
    "bitrate": "INTEGER",
    "sample_rate": "INTEGER",
    "bits_per_sample": "INTEGER",
    "channels": "INTEGER",
    "duration": "REAL",
    "title": "TEXT",
    "artist": "TEXT",
    "album": "TEXT",
    "album_artist": "TEXT",
    "track_number": "TEXT",
    "disc_number": "TEXT",
    "date": "TEXT",
    "musicbrainz_track_id": "TEXT",
    "musicbrainz_album_id": "TEXT",
    "musicbrainz_artist_id": "TEXT",
    "has_artwork": "INTEGER NOT NULL DEFAULT 0",
    "metadata_error": "TEXT",
    "analyzed_size": "INTEGER",
    "analyzed_modified_ns": "INTEGER",
    "analyzed_at": "TEXT",
}

SCAN_COLUMNS: dict[str, str] = {
    "files_analyzed": "INTEGER NOT NULL DEFAULT 0",
    "files_unchanged": "INTEGER NOT NULL DEFAULT 0",
}


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA temp_store=MEMORY")
        self._migrate()

    def _column_names(self, table: str) -> set[str]:
        rows = self.connection.execute(f"PRAGMA table_info({table})").fetchall()
        return {str(row["name"]) for row in rows}

    def _ensure_columns(self, table: str, columns: dict[str, str]) -> None:
        existing = self._column_names(table)
        for name, definition in columns.items():
            if name not in existing:
                self.connection.execute(
                    f'ALTER TABLE "{table}" ADD COLUMN "{name}" {definition}'
                )

    def _migrate(self) -> None:
        self.connection.executescript(BASE_SCHEMA)
        self._ensure_columns("files", FILE_COLUMNS)
        self._ensure_columns("scans", SCAN_COLUMNS)
        self.connection.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_files_content_hash
                ON files(content_hash);
            CREATE INDEX IF NOT EXISTS idx_files_album_artist_album
                ON files(album_artist, album);
            CREATE INDEX IF NOT EXISTS idx_files_analyzed_state
                ON files(analyzed_size, analyzed_modified_ns);
            """
        )
        self.connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> Database:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def start_scan(self, root_name: str, root_path: Path) -> int:
        cursor = self.connection.execute(
            "INSERT INTO scans(root_name, root_path) VALUES (?, ?)",
            (root_name, str(root_path)),
        )
        self.connection.commit()

        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return an ID for the newly created scan")

        return cursor.lastrowid

    def finish_scan(
        self,
        scan_id: int,
        *,
        files_seen: int,
        files_analyzed: int,
        files_unchanged: int,
        errors: int,
    ) -> None:
        self.connection.execute(
            """
            UPDATE scans
               SET completed_at = CURRENT_TIMESTAMP,
                   files_seen = ?,
                   files_analyzed = ?,
                   files_unchanged = ?,
                   errors = ?
             WHERE id = ?
            """,
            (files_seen, files_analyzed, files_unchanged, errors, scan_id),
        )
        self.connection.commit()

    def analysis_state(
        self,
        paths: Sequence[Path],
    ) -> dict[str, tuple[int | None, int | None]]:
        if not paths:
            return {}

        placeholders = ",".join("?" for _ in paths)
        rows = self.connection.execute(
            f"""
            SELECT path, analyzed_size, analyzed_modified_ns
              FROM files
             WHERE path IN ({placeholders})
            """,
            tuple(str(path) for path in paths),
        ).fetchall()

        return {
            str(row["path"]): (
                int(row["analyzed_size"]) if row["analyzed_size"] is not None else None,
                int(row["analyzed_modified_ns"])
                if row["analyzed_modified_ns"] is not None
                else None,
            )
            for row in rows
        }

    def upsert_inventory(self, records: Iterable[FileRecord]) -> None:
        self.connection.executemany(
            """
            INSERT INTO files(
                path, root_name, directory, filename, extension,
                size, modified_ns, inode, device
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                root_name = excluded.root_name,
                directory = excluded.directory,
                filename = excluded.filename,
                extension = excluded.extension,
                size = excluded.size,
                modified_ns = excluded.modified_ns,
                inode = excluded.inode,
                device = excluded.device,
                last_seen_at = CURRENT_TIMESTAMP
            """,
            (
                (
                    str(record.path),
                    record.root_name,
                    str(record.directory),
                    record.filename,
                    record.extension,
                    record.size,
                    record.modified_ns,
                    record.inode,
                    record.device,
                )
                for record in records
            ),
        )
        self.connection.commit()

    def save_analysis(self, records: Iterable[AnalyzedFile]) -> None:
        self.connection.executemany(
            """
            UPDATE files
               SET content_hash = ?,
                   hash_algorithm = ?,
                   codec = ?,
                   bitrate = ?,
                   sample_rate = ?,
                   bits_per_sample = ?,
                   channels = ?,
                   duration = ?,
                   title = ?,
                   artist = ?,
                   album = ?,
                   album_artist = ?,
                   track_number = ?,
                   disc_number = ?,
                   date = ?,
                   musicbrainz_track_id = ?,
                   musicbrainz_album_id = ?,
                   musicbrainz_artist_id = ?,
                   has_artwork = ?,
                   metadata_error = ?,
                   analyzed_size = ?,
                   analyzed_modified_ns = ?,
                   analyzed_at = CURRENT_TIMESTAMP
             WHERE path = ?
            """,
            (
                (
                    record.content_hash,
                    record.hash_algorithm,
                    record.metadata.codec,
                    record.metadata.bitrate,
                    record.metadata.sample_rate,
                    record.metadata.bits_per_sample,
                    record.metadata.channels,
                    record.metadata.duration,
                    record.metadata.title,
                    record.metadata.artist,
                    record.metadata.album,
                    record.metadata.album_artist,
                    record.metadata.track_number,
                    record.metadata.disc_number,
                    record.metadata.date,
                    record.metadata.musicbrainz_track_id,
                    record.metadata.musicbrainz_album_id,
                    record.metadata.musicbrainz_artist_id,
                    int(record.metadata.has_artwork),
                    record.metadata.error,
                    record.file.size,
                    record.file.modified_ns,
                    str(record.file.path),
                )
                for record in records
            ),
        )
        self.connection.commit()

    def stats(self) -> dict[str, int | float]:
        row = self.connection.execute(
            """
            SELECT
                COUNT(*) AS files,
                COALESCE(SUM(size), 0) AS bytes,
                COUNT(DISTINCT directory) AS directories,
                COUNT(content_hash) AS hashed,
                COUNT(analyzed_at) AS analyzed,
                COUNT(metadata_error) AS metadata_errors,
                COALESCE(SUM(duration), 0) AS duration
            FROM files
            """
        ).fetchone()
        assert row is not None
        return {
            "files": int(row["files"]),
            "bytes": int(row["bytes"]),
            "directories": int(row["directories"]),
            "hashed": int(row["hashed"]),
            "analyzed": int(row["analyzed"]),
            "metadata_errors": int(row["metadata_errors"]),
            "duration": float(row["duration"]),
        }

    def optimize(self) -> None:
        self.connection.execute("PRAGMA optimize")
        self.connection.execute("VACUUM")
