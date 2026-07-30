from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

from musicclean.models import FileRecord

SCHEMA = """
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
    files_changed INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0
);
"""


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA temp_store=MEMORY")
        self.connection.executescript(SCHEMA)

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
            
        return int(cursor.lastrowid)

    def finish_scan(
        self,
        scan_id: int,
        *,
        files_seen: int,
        files_changed: int,
        errors: int,
    ) -> None:
        self.connection.execute(
            """
            UPDATE scans
               SET completed_at = CURRENT_TIMESTAMP,
                   files_seen = ?,
                   files_changed = ?,
                   errors = ?
             WHERE id = ?
            """,
            (files_seen, files_changed, errors, scan_id),
        )
        self.connection.commit()

    def upsert_files(self, records: Iterable[FileRecord]) -> int:
        changed = 0
        for record in records:
            before = self.connection.total_changes
            self.connection.execute(
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
                WHERE files.size != excluded.size
                   OR files.modified_ns != excluded.modified_ns
                   OR files.inode != excluded.inode
                   OR files.device != excluded.device
                """,
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
                ),
            )
            if self.connection.total_changes > before:
                changed += 1
        self.connection.commit()
        return changed

    def stats(self) -> dict[str, int]:
        row = self.connection.execute(
            """
            SELECT
                COUNT(*) AS files,
                COALESCE(SUM(size), 0) AS bytes,
                COUNT(DISTINCT directory) AS directories
            FROM files
            """
        ).fetchone()
        assert row is not None
        return {"files": int(row[0]), "bytes": int(row[1]), "directories": int(row[2])}

    def optimize(self) -> None:
        self.connection.execute("PRAGMA optimize")
        self.connection.execute("VACUUM")
