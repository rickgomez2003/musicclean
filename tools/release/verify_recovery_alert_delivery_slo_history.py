"""Verify delivery SLO history/trend configuration."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []
    with (root / "release/recovery-alerting.toml").open("rb") as stream:
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        return ("recovery alerting policy is missing",)

    expected = {
        "schema_version": 1,
        "maximum_records": 52,
        "short_window": 4,
        "long_window": 12,
        "minimum_trend_samples": 4,
        "retain_days": 90,
        "deduplicate": True,
    }
    if alerting.get("slo_history") != expected:
        errors.append("recovery alert delivery SLO history policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "Collect prior delivery SLO evidence",
        "Build recovery alert delivery SLO history",
        "Analyze recovery alert delivery SLO trends",
        "Verify recovery alert delivery SLO history",
        "recovery-alert-delivery-slo-history.json",
        "recovery-alert-delivery-slo-trend.json",
        "recovery-alert-delivery-slo-trend-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"delivery SLO history workflow missing {fragment}")
    return tuple(errors)


def verify_trend(path: Path) -> tuple[str, ...]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load delivery SLO trend report: {exc}",)

    if not isinstance(report, dict):
        return ("delivery SLO trend report must be an object",)

    errors: list[str] = []
    for field in (
        "schema_version",
        "generated_at",
        "sample_count",
        "minimum_trend_samples",
        "status_counts",
        "consecutive_warn_fail",
        "trend_status",
        "metrics",
    ):
        if field not in report:
            errors.append(f"delivery SLO trend report missing field {field}")

    if report.get("trend_status") not in {
        "INSUFFICIENT_DATA",
        "improving",
        "stable",
        "worsening",
    }:
        errors.append("delivery SLO trend status is invalid")
    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trend", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())
    if args.trend is not None:
        errors.extend(verify_trend(args.trend))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        "recovery alert delivery SLO history and trend policy verified"
        if args.trend is None
        else f"recovery alert delivery SLO trend verified: {args.trend}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
