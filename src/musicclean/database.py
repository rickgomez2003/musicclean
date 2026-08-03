from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path

from musicclean.error_analysis import assess_metadata_error
from musicclean.models import (
    AnalyzedFile,
    DuplicateFile,
    DuplicateGroup,
    FileRecord,
    MetadataErrorRecord,
)

SCHEMA_VERSION = 4

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
            CREATE INDEX IF NOT EXISTS idx_files_hash_size
                ON files(content_hash, size);
            CREATE INDEX IF NOT EXISTS idx_files_album_artist_album
                ON files(album_artist, album);
            CREATE INDEX IF NOT EXISTS idx_files_analyzed_state
                ON files(analyzed_size, analyzed_modified_ns);
            CREATE INDEX IF NOT EXISTS idx_files_metadata_error
                ON files(metadata_error);
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

    def duplicate_summary(
        self,
        *,
        root_name: str | None = None,
        minimum_size: int = 1,
    ) -> dict[str, int]:
        parameters: list[object] = [minimum_size]
        root_clause = ""
        if root_name is not None:
            root_clause = "AND root_name = ?"
            parameters.append(root_name)

        row = self.connection.execute(
            f"""
            WITH duplicate_groups AS (
                SELECT content_hash, size, COUNT(*) AS file_count
                FROM files
                WHERE content_hash IS NOT NULL
                  AND size >= ?
                  {root_clause}
                GROUP BY content_hash, size
                HAVING COUNT(*) > 1
            )
            SELECT
                COUNT(*) AS groups,
                COALESCE(SUM(file_count), 0) AS duplicate_files,
                COALESCE(SUM(size * (file_count - 1)), 0) AS reclaimable_bytes
            FROM duplicate_groups
            """,
            parameters,
        ).fetchone()
        assert row is not None

        return {
            "groups": int(row["groups"]),
            "duplicate_files": int(row["duplicate_files"]),
            "reclaimable_bytes": int(row["reclaimable_bytes"]),
        }

    def iter_duplicate_groups(
        self,
        *,
        root_name: str | None = None,
        minimum_size: int = 1,
        limit: int | None = None,
    ) -> Iterator[DuplicateGroup]:
        parameters: list[object] = [minimum_size]
        root_filter = ""
        member_filter = ""

        if root_name is not None:
            root_filter = "AND root_name = ?"
            member_filter = "AND f.root_name = ?"
            parameters.append(root_name)

        limit_clause = ""
        if limit is not None:
            limit_clause = "LIMIT ?"
            parameters.append(limit)

        group_rows = self.connection.execute(
            f"""
            SELECT
                content_hash,
                COALESCE(hash_algorithm, 'unknown') AS hash_algorithm,
                size,
                COUNT(*) AS file_count
            FROM files
            WHERE content_hash IS NOT NULL
              AND size >= ?
              {root_filter}
            GROUP BY content_hash, hash_algorithm, size
            HAVING COUNT(*) > 1
            ORDER BY (size * (COUNT(*) - 1)) DESC, content_hash
            {limit_clause}
            """,
            parameters,
        ).fetchall()

        for group_row in group_rows:
            content_hash = str(group_row["content_hash"])
            size = int(group_row["size"])
            member_parameters: list[object] = [content_hash, size]

            if root_name is not None:
                member_parameters.append(root_name)

            file_rows = self.connection.execute(
                f"""
                SELECT
                    f.path,
                    f.root_name,
                    f.filename,
                    f.extension,
                    f.size,
                    f.modified_ns,
                    f.codec,
                    f.bitrate,
                    f.sample_rate,
                    f.bits_per_sample,
                    f.duration
                FROM files AS f
                WHERE f.content_hash = ?
                  AND f.size = ?
                  {member_filter}
                ORDER BY f.root_name, f.path
                """,
                member_parameters,
            ).fetchall()

            files = tuple(
                DuplicateFile(
                    path=Path(str(row["path"])),
                    root_name=str(row["root_name"]),
                    filename=str(row["filename"]),
                    extension=str(row["extension"]),
                    size=int(row["size"]),
                    modified_ns=int(row["modified_ns"]),
                    codec=str(row["codec"]) if row["codec"] is not None else None,
                    bitrate=int(row["bitrate"]) if row["bitrate"] is not None else None,
                    sample_rate=(
                        int(row["sample_rate"])
                        if row["sample_rate"] is not None
                        else None
                    ),
                    bits_per_sample=(
                        int(row["bits_per_sample"])
                        if row["bits_per_sample"] is not None
                        else None
                    ),
                    duration=(
                        float(row["duration"]) if row["duration"] is not None else None
                    ),
                )
                for row in file_rows
            )

            yield DuplicateGroup(
                content_hash=content_hash,
                hash_algorithm=str(group_row["hash_algorithm"]),
                size=size,
                files=files,
            )

    def metadata_error_summary(
        self,
        *,
        root_name: str | None = None,
    ) -> dict[str, int]:
        parameters: list[object] = []
        root_clause = ""
        if root_name is not None:
            root_clause = "AND root_name = ?"
            parameters.append(root_name)

        rows = self.connection.execute(
            f"""
            SELECT metadata_error
            FROM files
            WHERE metadata_error IS NOT NULL
              AND TRIM(metadata_error) <> ''
              {root_clause}
            """,
            parameters,
        ).fetchall()

        summary: dict[str, int] = {}
        for row in rows:
            assessment = assess_metadata_error(str(row["metadata_error"]))
            key = assessment.category.value
            summary[key] = summary.get(key, 0) + 1
        return summary

    def metadata_errors(
        self,
        *,
        root_name: str | None = None,
        category: str | None = None,
        limit: int | None = 200,
    ) -> list[MetadataErrorRecord]:
        parameters: list[object] = []
        root_clause = ""
        if root_name is not None:
            root_clause = "AND root_name = ?"
            parameters.append(root_name)

        rows = self.connection.execute(
            f"""
            SELECT path, root_name, extension, size, codec, metadata_error
            FROM files
            WHERE metadata_error IS NOT NULL
              AND TRIM(metadata_error) <> ''
              {root_clause}
            ORDER BY size DESC, path
            """,
            parameters,
        ).fetchall()

        results: list[MetadataErrorRecord] = []
        for row in rows:
            error = str(row["metadata_error"])
            assessment = assess_metadata_error(error)
            if category is not None and assessment.category.value != category:
                continue

            results.append(
                MetadataErrorRecord(
                    path=Path(str(row["path"])),
                    root_name=str(row["root_name"]),
                    extension=str(row["extension"]),
                    size=int(row["size"]),
                    codec=str(row["codec"]) if row["codec"] is not None else None,
                    error=error,
                    category=assessment.category.value,
                    suggested_action=assessment.suggested_action,
                )
            )

            if limit is not None and len(results) >= limit:
                break

        return results

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

    def album_rows(
        self,
        *,
        root_name: str | None = None,
        artist: str | None = None,
        album: str | None = None,
    ) -> list[dict[str, object]]:
        clauses = ["album IS NOT NULL", "TRIM(album) <> ''"]
        parameters: list[object] = []
        if root_name is not None:
            clauses.append("root_name = ?")
            parameters.append(root_name)
        if artist is not None:
            clauses.append("LOWER(COALESCE(album_artist, artist, '')) LIKE LOWER(?)")
            parameters.append(f"%{artist}%")
        if album is not None:
            clauses.append("LOWER(album) LIKE LOWER(?)")
            parameters.append(f"%{album}%")
        rows = self.connection.execute(
            f"""
            SELECT path, directory, extension, artist, album_artist, album, title,
                   track_number, sample_rate, bits_per_sample, bitrate, has_artwork,
                   musicbrainz_track_id, musicbrainz_album_id, metadata_error
              FROM files
             WHERE {' AND '.join(clauses)}
             ORDER BY COALESCE(album_artist, artist), album, directory, track_number, path
            """,
            parameters,
        ).fetchall()
        return [dict(row) for row in rows]

    def optimize(self) -> None:
        self.connection.execute("PRAGMA optimize")
        self.connection.execute("VACUUM")
