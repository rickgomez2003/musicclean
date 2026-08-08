"""Build bounded, deduplicated routed-delivery SLO history."""

from __future__ import annotations

import argparse
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

    policy = alerting.get("routed_delivery_slo_history")
    if not isinstance(policy, dict):
        raise ValueError("alerting.routed_delivery_slo_history policy is missing")

    return policy


def _history_reports(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        return []

    reports: list[dict[str, Any]] = []
    for path in sorted(root.rglob("recovery-alert-routed-delivery-slo.json")):
        try:
            reports.append(_load_json(path))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return reports


def _record_key(report: dict[str, Any]) -> str:
    generated_at = str(report.get("generated_at", ""))
    route = str(report.get("current_route", ""))
    severity = str(report.get("current_severity", ""))
    sample_count = str(report.get("sample_count", ""))
    return f"{generated_at}|{route}|{severity}|{sample_count}"


def _safe_record(report: dict[str, Any]) -> dict[str, Any]:
    evaluations = []
    raw_evaluations = report.get("evaluations")
    if isinstance(raw_evaluations, list):
        for item in raw_evaluations:
            if not isinstance(item, dict):
                continue
            evaluations.append(
                {
                    "metric": item.get("metric"),
                    "value": item.get("value"),
                    "status": item.get("status"),
                    "direction": item.get("direction"),
                }
            )

    return {
        "generated_at": report.get("generated_at"),
        "sample_count": report.get("sample_count"),
        "minimum_samples": report.get("minimum_samples"),
        "authoritative": bool(report.get("authoritative")),
        "sample_gate": report.get("sample_gate"),
        "status": report.get("status"),
        "current_route": report.get("current_route"),
        "current_severity": report.get("current_severity"),
        "evaluations": evaluations,
    }


def build_history(
    current: dict[str, Any],
    prior: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    history_limit = max(int(policy.get("history_limit", 52)), 1)

    deduplicated: dict[str, dict[str, Any]] = {}
    for report in [*prior, current]:
        deduplicated[_record_key(report)] = _safe_record(report)

    records = sorted(
        deduplicated.values(),
        key=lambda item: str(item.get("generated_at", "")),
    )[-history_limit:]

    return {
        "schema_version": 1,
        "history_limit": history_limit,
        "record_count": len(records),
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--history-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    history = build_history(
        _load_json(args.report),
        _history_reports(args.history_root),
        _load_policy(args.policy),
    )

    args.output.write_text(
        json.dumps(history, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
