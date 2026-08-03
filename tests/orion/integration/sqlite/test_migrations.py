from pathlib import Path

from musicclean.orion.adapters.sqlite import CURRENT_SCHEMA_VERSION, connect_sqlite, migrate


def test_migrate_creates_schema_and_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    connection = connect_sqlite(db_path)
    try:
        assert migrate(connection) == CURRENT_SCHEMA_VERSION
        assert migrate(connection) == CURRENT_SCHEMA_VERSION

        version = connection.execute("SELECT MAX(version) FROM orion_schema_migrations").fetchone()[
            0
        ]
        assert int(version) == CURRENT_SCHEMA_VERSION

        tables = {
            str(row[0])
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "orion_albums" in tables
        assert "orion_editions" in tables
        assert "orion_discs" in tables
        assert "orion_recordings" in tables
        assert "orion_track_appearances" in tables
        assert "orion_audio_files" in tables
    finally:
        connection.close()
