"""Build bounded recovery alert delivery SLO history."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def build_history(
    prior_root: Path,
    current: dict[str, Any],
    maximum_records: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if prior_root.exists():
        for path in sorted(prior_root.rglob("recovery-alert-delivery-slo.json")):
            try:
                records.append(_load(path))
            except (OSError, ValueError, json.JSONDecodeError):
                continue

    records.append(current)
    unique: dict[tuple[object, object], dict[str, Any]] = {}
    for record in records:
        key = (record.get("generated_at"), record.get("status"))
        unique[key] = record

    ordered = sorted(unique.values(), key=lambda item: str(item.get("generated_at", "")))
    return ordered[-maximum_records:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-root", type=Path, required=True)
    parser.add_argument("--current-report", type=Path, required=True)
    parser.add_argument("--maximum-records", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    records = build_history(
        args.prior_root,
        _load(args.current_report),
        args.maximum_records,
    )
    args.output.write_text(
        json.dumps(
            {"schema_version": 1, "record_count": len(records), "records": records},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
