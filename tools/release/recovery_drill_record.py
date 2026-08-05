"""Create and update machine-readable recovery drill records."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now() -> datetime:
    return datetime.now(UTC)


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("recovery drill record must be an object")
    return data


def _write(path: Path, record: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def start(
    path: Path,
    *,
    tag: str,
    retention_class: str,
    run_id: int,
    repository: str,
) -> dict[str, Any]:
    started = _now()
    record = {
        "schema_version": 1,
        "drill_id": f"{repository}:{run_id}",
        "repository": repository,
        "run_id": run_id,
        "tag": tag,
        "retention_class": retention_class,
        "started_at": started.isoformat(),
        "completed_at": None,
        "elapsed_seconds": None,
        "status": "RUNNING",
        "restore_receipt": None,
        "failure_reason": None,
    }
    _write(path, record)
    return record


def complete(
    path: Path,
    restore_receipt_path: Path,
) -> dict[str, Any]:
    record = _load(path)
    receipt = _load(restore_receipt_path)

    started_at = record.get("started_at")
    if not isinstance(started_at, str):
        raise ValueError("recovery drill record is missing started_at")

    started = datetime.fromisoformat(started_at)
    completed = _now()
    elapsed = max(0.0, (completed - started).total_seconds())

    if receipt.get("safe_extract") is not True:
        raise ValueError("restore receipt does not prove safe extraction")
    if receipt.get("download_verified") is not True:
        raise ValueError("restore receipt does not prove download verification")
    if receipt.get("remote_verified") is not True:
        raise ValueError("restore receipt does not prove remote verification")

    record["completed_at"] = completed.isoformat()
    record["elapsed_seconds"] = elapsed
    record["status"] = "PASS"
    record["restore_receipt"] = receipt
    record["failure_reason"] = None
    _write(path, record)
    return record


def fail(path: Path, reason: str) -> dict[str, Any]:
    record = _load(path)
    started_at = record.get("started_at")
    if not isinstance(started_at, str):
        raise ValueError("recovery drill record is missing started_at")

    completed = _now()
    elapsed = max(
        0.0,
        (completed - datetime.fromisoformat(started_at)).total_seconds(),
    )

    record["completed_at"] = completed.isoformat()
    record["elapsed_seconds"] = elapsed
    record["status"] = "FAIL"
    record["failure_reason"] = reason
    _write(path, record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    start_parser = sub.add_parser("start")
    start_parser.add_argument("--record", type=Path, required=True)
    start_parser.add_argument("--tag", required=True)
    start_parser.add_argument("--retention-class", required=True)
    start_parser.add_argument("--run-id", type=int, required=True)
    start_parser.add_argument("--repository", required=True)

    complete_parser = sub.add_parser("complete")
    complete_parser.add_argument("--record", type=Path, required=True)
    complete_parser.add_argument("--restore-receipt", type=Path, required=True)

    fail_parser = sub.add_parser("fail")
    fail_parser.add_argument("--record", type=Path, required=True)
    fail_parser.add_argument("--reason", required=True)

    args = parser.parse_args()

    if args.command == "start":
        start(
            args.record,
            tag=args.tag,
            retention_class=args.retention_class,
            run_id=args.run_id,
            repository=args.repository,
        )
    elif args.command == "complete":
        complete(args.record, args.restore_receipt)
    else:
        fail(args.record, args.reason)

    print(args.record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
