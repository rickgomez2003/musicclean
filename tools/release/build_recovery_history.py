"""Build bounded recovery drill history from prior artifact records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_record(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if not isinstance(data.get("drill_id"), str):
        return None
    if not isinstance(data.get("completed_at"), str):
        return None
    if data.get("status") not in {"PASS", "FAIL"}:
        return None
    return data


def build_history(
    *,
    prior_root: Path,
    current_record: Path,
    maximum_records: int,
) -> list[dict[str, Any]]:
    if maximum_records < 1:
        raise ValueError("maximum_records must be positive")

    records: list[dict[str, Any]] = []

    if prior_root.exists():
        for path in sorted(prior_root.rglob("recovery-drill.json")):
            record = _load_record(path)
            if record is not None:
                records.append(record)

    current = _load_record(current_record)
    if current is None:
        raise ValueError("current recovery drill record is invalid")
    records.append(current)

    deduplicated: dict[str, dict[str, Any]] = {}
    for record in records:
        drill_id = str(record["drill_id"])
        existing = deduplicated.get(drill_id)
        if existing is None or str(record["completed_at"]) >= str(existing["completed_at"]):
            deduplicated[drill_id] = record

    ordered = sorted(
        deduplicated.values(),
        key=lambda item: str(item["completed_at"]),
    )
    return ordered[-maximum_records:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-root", type=Path, required=True)
    parser.add_argument("--current-record", type=Path, required=True)
    parser.add_argument("--maximum-records", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    history = build_history(
        prior_root=args.prior_root,
        current_record=args.current_record,
        maximum_records=args.maximum_records,
    )
    args.output.write_text(
        json.dumps(history, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"{args.output}: {len(history)} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
