from pathlib import Path

from musicclean.database import Database
from musicclean.models import AnalyzedFile, AudioMetadata, FileRecord


def make_record(tmp_path: Path, name: str, size: int, modified_ns: int) -> FileRecord:
    path = tmp_path / name
    return FileRecord(
        path=path,
        root_name="library",
        directory=path.parent,
        filename=path.name,
        extension=path.suffix,
        size=size,
        modified_ns=modified_ns,
        inode=modified_ns,
        device=1,
    )


def analyze(record: FileRecord, content_hash: str) -> AnalyzedFile:
    return AnalyzedFile(
        file=record,
        metadata=AudioMetadata(codec="FLAC", duration=120.0),
        content_hash=content_hash,
        hash_algorithm="blake3",
    )


def test_duplicate_summary_and_groups(tmp_path: Path) -> None:
    records = [
        make_record(tmp_path, "one.flac", 1000, 1),
        make_record(tmp_path, "two.flac", 1000, 2),
        make_record(tmp_path, "three.flac", 1000, 3),
        make_record(tmp_path, "unique.flac", 500, 4),
    ]

    with Database(tmp_path / "test.db") as database:
        database.upsert_inventory(records)
        database.save_analysis(
            [
                analyze(records[0], "duplicate-hash"),
                analyze(records[1], "duplicate-hash"),
                analyze(records[2], "duplicate-hash"),
                analyze(records[3], "unique-hash"),
            ]
        )

        summary = database.duplicate_summary()
        assert summary == {
            "groups": 1,
            "duplicate_files": 3,
            "reclaimable_bytes": 2000,
        }

        groups = list(database.iter_duplicate_groups())
        assert len(groups) == 1
        assert groups[0].file_count == 3
        assert groups[0].reclaimable_bytes == 2000
        assert {file.filename for file in groups[0].files} == {
            "one.flac",
            "two.flac",
            "three.flac",
        }


def test_duplicate_filters(tmp_path: Path) -> None:
    first = make_record(tmp_path, "one.flac", 100, 1)
    second = make_record(tmp_path, "two.flac", 100, 2)

    with Database(tmp_path / "test.db") as database:
        database.upsert_inventory([first, second])
        database.save_analysis(
            [
                analyze(first, "same"),
                analyze(second, "same"),
            ]
        )

        assert database.duplicate_summary(minimum_size=101)["groups"] == 0
        assert database.duplicate_summary(root_name="downloads")["groups"] == 0
