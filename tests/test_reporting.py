import csv
import json
from pathlib import Path

from musicclean.models import DuplicateFile, DuplicateGroup
from musicclean.reporting import write_csv_report, write_json_report


def sample_group(tmp_path: Path) -> DuplicateGroup:
    files = (
        DuplicateFile(
            path=tmp_path / "a.flac",
            root_name="library",
            filename="a.flac",
            extension=".flac",
            size=100,
            modified_ns=1,
            codec="FLAC",
            bitrate=1000,
            sample_rate=44100,
            bits_per_sample=16,
            duration=60.0,
        ),
        DuplicateFile(
            path=tmp_path / "b.flac",
            root_name="library",
            filename="b.flac",
            extension=".flac",
            size=100,
            modified_ns=2,
            codec="FLAC",
            bitrate=1000,
            sample_rate=44100,
            bits_per_sample=16,
            duration=60.0,
        ),
    )
    return DuplicateGroup(
        content_hash="abc",
        hash_algorithm="blake3",
        size=100,
        files=files,
    )


def test_json_report(tmp_path: Path) -> None:
    output = tmp_path / "duplicates.json"
    write_json_report([sample_group(tmp_path)], output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["report_type"] == "exact_duplicates"
    assert payload["groups"][0]["reclaimable_bytes"] == 100
    assert len(payload["groups"][0]["files"]) == 2


def test_csv_report(tmp_path: Path) -> None:
    output = tmp_path / "duplicates.csv"
    write_csv_report([sample_group(tmp_path)], output)

    with output.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 2
    assert rows[0]["group_hash"] == "abc"
    assert rows[0]["group_reclaimable_bytes"] == "100"
