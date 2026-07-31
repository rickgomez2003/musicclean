from pathlib import Path

from musicclean.database import Database
from musicclean.models import AnalyzedFile, AudioMetadata, FileRecord


def make_file(tmp_path: Path, name: str) -> FileRecord:
    path = tmp_path / name
    return FileRecord(
        path=path,
        root_name="downloads",
        directory=path.parent,
        filename=path.name,
        extension=path.suffix,
        size=100,
        modified_ns=1,
        inode=1,
        device=1,
    )


def test_metadata_error_query_and_summary(tmp_path: Path) -> None:
    record = make_file(tmp_path, "bad.flac")

    with Database(tmp_path / "test.db") as database:
        database.upsert_inventory([record])
        database.save_analysis(
            [
                AnalyzedFile(
                    file=record,
                    metadata=AudioMetadata(
                        codec="FLAC",
                        error="unexpected end of file",
                    ),
                    content_hash="abc",
                    hash_algorithm="blake3",
                )
            ]
        )

        summary = database.metadata_error_summary()
        records = database.metadata_errors()

    assert summary["truncated_file"] == 1
    assert len(records) == 1
    assert records[0].category == "truncated_file"
    assert records[0].path.name == "bad.flac"


def test_category_filter(tmp_path: Path) -> None:
    record = make_file(tmp_path, "bad.wv")

    with Database(tmp_path / "test.db") as database:
        database.upsert_inventory([record])
        database.save_analysis(
            [
                AnalyzedFile(
                    file=record,
                    metadata=AudioMetadata(error="Permission denied"),
                    content_hash="abc",
                    hash_algorithm="blake3",
                )
            ]
        )

        assert len(database.metadata_errors(category="access_failure")) == 1
        assert database.metadata_errors(category="truncated_file") == []
