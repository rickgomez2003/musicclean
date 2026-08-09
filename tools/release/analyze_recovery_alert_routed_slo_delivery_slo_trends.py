"""Analyze trends across routed SLO alert delivery SLO history."""

from __future__ import annotations

import argparse
import json
import tomllib
from datetime import UTC, datetime
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


def _severity(status: str) -> int:
    return {
        "PASS": 0,
        "WARN": 1,
        "FAIL": 2,
        "INSUFFICIENT_SAMPLES": 0,
    }.get(status, 0)


def analyze(
    history: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    records = history.get("records")
    if not isinstance(records, list):
        raise ValueError("history records must be a list")

    authoritative = [
        item for item in records if isinstance(item, dict) and bool(item.get("authoritative"))
    ]

    minimum = int(policy.get("minimum_trend_samples", 4))
    short_window = int(policy.get("short_window", 2))
    long_window = int(policy.get("long_window", 4))

    if len(authoritative) < minimum:
        trend = "INSUFFICIENT_SAMPLES"
        recent_score = None
        baseline_score = None
        is_authoritative = False
    else:
        recent = authoritative[-short_window:]
        baseline_source = authoritative[:-short_window]
        baseline = baseline_source[-long_window:]

        recent_score = sum(_severity(str(item.get("status"))) for item in recent) / len(recent)

        if baseline:
            baseline_score = sum(_severity(str(item.get("status"))) for item in baseline) / len(
                baseline
            )
        else:
            baseline_score = recent_score

        if recent_score > baseline_score:
            trend = "WORSENING"
        elif recent_score < baseline_score:
            trend = "IMPROVING"
        else:
            trend = "STABLE"

        is_authoritative = True

    current_status = (
        str(authoritative[-1].get("status")) if authoritative else "INSUFFICIENT_SAMPLES"
    )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "authoritative": is_authoritative,
        "sample_count": len(authoritative),
        "minimum_trend_samples": minimum,
        "trend": trend,
        "recent_severity_score": recent_score,
        "baseline_severity_score": baseline_score,
        "current_status": current_status,
    }


def render_summary(report: dict[str, Any]) -> str:
    return (
        "## Routed SLO Alert Delivery SLO History & Trends\n\n"
        f"- Trend: {report['trend']}\n"
        f"- Authoritative: {str(report['authoritative']).lower()}\n"
        f"- Sample count: {report['sample_count']}\n"
        f"- Current status: {report['current_status']}\n"
        f"- Recent severity score: {report['recent_severity_score']}\n"
        f"- Baseline severity score: {report['baseline_severity_score']}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    report = analyze(
        _load_json(args.history),
        _load_policy(args.policy),
    )

    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.summary.write_text(
        render_summary(report),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
