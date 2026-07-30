from pathlib import Path

from musicclean.database import SCHEMA_VERSION, Database
from musicclean.models import AnalyzedFile, AudioMetadata, FileRecord


def make_record(tmp_path: Path) -> FileRecord:
    return FileRecord(
        path=tmp_path / "album" / "track.flac",
        root_name="library",
        directory=tmp_path / "album",
        filename="track.flac",
        extension=".flac",
        size=1234,
        modified_ns=123456789,
        inode=1,
        device=2,
    )


def test_inventory_analysis_and_stats(tmp_path: Path) -> None:
    db_path = tmp_path / "musicclean.db"
    record = make_record(tmp_path)

    analyzed = AnalyzedFile(
        file=record,
        metadata=AudioMetadata(
            codec="FLAC",
            sample_rate=96000,
            bits_per_sample=24,
            channels=2,
            duration=180.5,
            title="Track",
            artist="Artist",
            album="Album",
            has_artwork=True,
        ),
        content_hash="abc123",
        hash_algorithm="blake3",
    )

    with Database(db_path) as database:
        database.upsert_inventory([record])
        assert database.analysis_state([record.path]) == {
            str(record.path): (None, None)
        }

        database.save_analysis([analyzed])
        assert database.analysis_state([record.path]) == {
            str(record.path): (record.size, record.modified_ns)
        }

        stats = database.stats()
        assert stats["files"] == 1
        assert stats["analyzed"] == 1
        assert stats["hashed"] == 1
        assert stats["duration"] == 180.5

        version = database.connection.execute("PRAGMA user_version").fetchone()[0]
        assert version == SCHEMA_VERSION


def test_existing_sprint_one_database_is_migrated(tmp_path: Path) -> None:
    db_path = tmp_path / "old.db"

    import sqlite3

    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE files (
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

        CREATE TABLE scans (
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
    )
    connection.close()

    with Database(db_path) as database:
        file_columns = {
            row["name"]
            for row in database.connection.execute("PRAGMA table_info(files)")
        }
        scan_columns = {
            row["name"]
            for row in database.connection.execute("PRAGMA table_info(scans)")
        }

        assert "content_hash" in file_columns
        assert "codec" in file_columns
        assert "analyzed_at" in file_columns
        assert "files_analyzed" in scan_columns
        assert "files_unchanged" in scan_columns
