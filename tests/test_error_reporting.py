import csv
import json
from pathlib import Path

from musicclean.error_reporting import (
    write_metadata_errors_csv,
    write_metadata_errors_json,
)
from musicclean.models import MetadataErrorRecord


def sample(tmp_path: Path) -> MetadataErrorRecord:
    return MetadataErrorRecord(
        path=tmp_path / "bad.flac",
        root_name="downloads",
        extension=".flac",
        size=100,
        codec="FLAC",
        error="unexpected end of file",
        category="truncated_file",
        suggested_action="Verify or re-download.",
    )


def test_json_report(tmp_path: Path) -> None:
    output = tmp_path / "errors.json"
    write_metadata_errors_json([sample(tmp_path)], output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["count"] == 1
    assert payload["errors"][0]["category"] == "truncated_file"


def test_csv_report(tmp_path: Path) -> None:
    output = tmp_path / "errors.csv"
    write_metadata_errors_csv([sample(tmp_path)], output)
    with output.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["category"] == "truncated_file"
