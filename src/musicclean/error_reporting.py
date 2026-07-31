from __future__ import annotations

import csv
import json
from pathlib import Path

from musicclean.models import MetadataErrorRecord


def write_metadata_errors_json(
    records: list[MetadataErrorRecord],
    output: Path,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "report_type": "metadata_errors",
        "count": len(records),
        "errors": [
            {
                "path": str(record.path),
                "root_name": record.root_name,
                "extension": record.extension,
                "size": record.size,
                "codec": record.codec,
                "category": record.category,
                "error": record.error,
                "suggested_action": record.suggested_action,
            }
            for record in records
        ],
    }
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_metadata_errors_csv(
    records: list[MetadataErrorRecord],
    output: Path,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "path",
                "root_name",
                "extension",
                "size",
                "codec",
                "category",
                "error",
                "suggested_action",
            ]
        )
        for record in records:
            writer.writerow(
                [
                    str(record.path),
                    record.root_name,
                    record.extension,
                    record.size,
                    record.codec,
                    record.category,
                    record.error,
                    record.suggested_action,
                ]
            )
