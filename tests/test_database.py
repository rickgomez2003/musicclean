from pathlib import Path

from musicclean.database import Database
from musicclean.models import FileRecord


def test_upsert_and_stats(tmp_path: Path) -> None:
    db_path = tmp_path / "musicclean.db"
    record = FileRecord(
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

    with Database(db_path) as database:
        assert database.upsert_files([record]) == 1
        assert database.upsert_files([record]) == 0
        assert database.stats()["files"] == 1
