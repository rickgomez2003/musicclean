"""Verify recovery SLO history/trend policy and workflow integration."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    policy_path = root / "release" / "recovery-history.toml"
    try:
        with policy_path.open("rb") as stream:
            doc = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return (f"unable to load recovery history policy: {exc}",)

    history = doc.get("history")
    expected = {
        "schema_version": 1,
        "maximum_records": 52,
        "minimum_trend_samples": 4,
        "short_window": 4,
        "long_window": 12,
        "artifact_lookup_runs": 52,
        "deduplicate_by": "drill_id",
        "sort_by": "completed_at",
    }
    if history != expected:
        errors.append("recovery history policy does not match expected values")

    workflow_path = root / ".github" / "workflows" / "orion-recovery-drill.yml"
    workflow = workflow_path.read_text(encoding="utf-8")

    required = (
        "actions: read",
        "Collect prior recovery drill artifacts",
        "gh run list",
        "gh run download",
        "Build recovery drill history",
        "build_recovery_history.py",
        "Analyze recovery trends",
        "analyze_recovery_trends.py",
        "recovery-slo-trend.json",
        "Verify recovery SLO history",
        "verify_recovery_slo_history.py",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"recovery workflow missing history integration {fragment}")

    ordered = (
        "Complete recovery drill",
        "Collect prior recovery drill artifacts",
        "Build recovery drill history",
        "Evaluate recovery SLOs",
        "Analyze recovery trends",
        "Verify recovery SLO report",
        "Verify recovery SLO history",
        "Upload recovery drill evidence",
    )
    positions = [workflow.find(step) for step in ordered]
    if any(position == -1 for position in positions):
        errors.append("recovery history workflow ordering cannot be verified")
    elif positions != sorted(positions):
        errors.append("recovery history workflow ordering is invalid")

    forbidden = (
        "contents: write",
        "gh release edit",
        "gh release create",
        "gh release upload",
        "git tag",
        "git push",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "--admin",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"recovery history workflow contains forbidden pattern {fragment}")

    return tuple(errors)


def verify_trend(path: Path) -> tuple[str, ...]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load recovery trend report: {exc}",)
    if not isinstance(report, dict):
        return ("recovery trend report must be an object",)

    errors: list[str] = []
    for field in (
        "schema_version",
        "records_available",
        "latest_drill_id",
        "short_window",
        "long_window",
        "duration_trend",
    ):
        if field not in report:
            errors.append(f"recovery trend report missing field {field}")

    if report.get("schema_version") != 1:
        errors.append("recovery trend schema version must be 1")
    if report.get("duration_trend") not in {
        "IMPROVING",
        "STABLE",
        "WORSENING",
        "INSUFFICIENT_DATA",
    }:
        errors.append("recovery duration trend is invalid")
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

    if args.trend is None:
        print("recovery SLO history and trend policy verified")
    else:
        print(f"recovery SLO trend verified: {args.trend}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
