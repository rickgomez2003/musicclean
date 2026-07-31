from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from musicclean.models import DuplicateGroup


def _group_dict(group: DuplicateGroup) -> dict[str, Any]:
    return {
        "content_hash": group.content_hash,
        "hash_algorithm": group.hash_algorithm,
        "size": group.size,
        "file_count": group.file_count,
        "reclaimable_bytes": group.reclaimable_bytes,
        "files": [
            {
                **asdict(file),
                "path": str(file.path),
            }
            for file in group.files
        ],
    }


def write_json_report(groups: Iterable[DuplicateGroup], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "report_type": "exact_duplicates",
        "groups": [_group_dict(group) for group in groups],
    }
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_csv_report(groups: Iterable[DuplicateGroup], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "group_hash",
        "hash_algorithm",
        "group_size",
        "group_file_count",
        "group_reclaimable_bytes",
        "path",
        "root_name",
        "filename",
        "extension",
        "size",
        "modified_ns",
        "codec",
        "bitrate",
        "sample_rate",
        "bits_per_sample",
        "duration",
    ]

    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for group in groups:
            for file in group.files:
                writer.writerow(
                    {
                        "group_hash": group.content_hash,
                        "hash_algorithm": group.hash_algorithm,
                        "group_size": group.size,
                        "group_file_count": group.file_count,
                        "group_reclaimable_bytes": group.reclaimable_bytes,
                        "path": str(file.path),
                        "root_name": file.root_name,
                        "filename": file.filename,
                        "extension": file.extension,
                        "size": file.size,
                        "modified_ns": file.modified_ns,
                        "codec": file.codec,
                        "bitrate": file.bitrate,
                        "sample_rate": file.sample_rate,
                        "bits_per_sample": file.bits_per_sample,
                        "duration": file.duration,
                    }
                )
