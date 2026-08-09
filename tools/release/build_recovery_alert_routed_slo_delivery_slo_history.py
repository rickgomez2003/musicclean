"""Build bounded, deduplicated history for routed SLO alert delivery SLO reports."""

from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_policy(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("alerting policy is missing")

    policy = alerting.get("routed_slo_alert_delivery_slo_history")
    if not isinstance(policy, dict):
        raise ValueError("routed SLO alert delivery SLO history policy is missing")

    return policy


def _fingerprint(report: dict[str, Any]) -> str:
    normalized = {
        "delivery_id": report.get("delivery_id"),
        "route": report.get("route"),
        "status": report.get("status"),
        "authoritative": report.get("authoritative"),
        "sample_count": report.get("sample_count"),
        "metrics": report.get("metrics"),
    }
    encoded = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_history(
    current: dict[str, Any],
    existing: dict[str, Any] | None,
    policy: dict[str, Any],
) -> dict[str, Any]:
    maximum = int(policy.get("max_records", 52))

    records: list[dict[str, Any]] = []
    if isinstance(existing, dict):
        raw_records = existing.get("records")
        if isinstance(raw_records, list):
            records = [item for item in raw_records if isinstance(item, dict)]

    current_record = dict(current)
    current_record["fingerprint"] = _fingerprint(current)

    by_fingerprint: dict[str, dict[str, Any]] = {}
    order: list[str] = []

    for record in [*records, current_record]:
        fingerprint = record.get("fingerprint")
        if not isinstance(fingerprint, str):
            fingerprint = _fingerprint(record)
            record = dict(record)
            record["fingerprint"] = fingerprint

        if fingerprint not in by_fingerprint:
            order.append(fingerprint)

        by_fingerprint[fingerprint] = record

    deduplicated = [by_fingerprint[fingerprint] for fingerprint in order][-maximum:]

    return {
        "schema_version": 1,
        "max_records": maximum,
        "record_count": len(deduplicated),
        "records": deduplicated,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--existing", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    existing = None
    if args.existing is not None and args.existing.exists():
        existing = _load_json(args.existing)

    history = build_history(
        _load_json(args.current),
        existing,
        _load_policy(args.policy),
    )

    args.output.write_text(
        json.dumps(history, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
