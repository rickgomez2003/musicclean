"""Verify recovery alert delivery SLO policy and report."""

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
        doc = tomllib.load(stream)
    alerting = doc.get("alerting")
    if not isinstance(alerting, dict):
        return ("recovery alerting policy is missing",)
    expected = {
        "schema_version": 1,
        "minimum_samples": 4,
        "publish_step_summary": True,
        "retain_days": 90,
        "success_rate": {"warn_below": 0.99, "fail_below": 0.95},
        "retry_rate": {"warn_above": 0.10, "fail_above": 0.25},
        "terminal_failure_rate": {"warn_above": 0.02, "fail_above": 0.05},
        "average_latency_seconds": {"warn_above": 5.0, "fail_above": 10.0},
    }
    if alerting.get("slos") != expected:
        errors.append("recovery alert delivery SLO policy is invalid")
    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "Evaluate recovery alert delivery SLOs",
        "evaluate_recovery_alert_delivery_slos.py",
        "Verify recovery alert delivery SLOs",
        "verify_recovery_alert_delivery_slos.py",
        "recovery-alert-delivery-slo.json",
        "recovery-alert-delivery-slo-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"recovery alert delivery SLO workflow missing {fragment}")
    return tuple(errors)


def verify_report(path: Path) -> tuple[str, ...]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load recovery alert delivery SLO report: {exc}",)
    if not isinstance(report, dict):
        return ("recovery alert delivery SLO report must be an object",)
    errors: list[str] = []
    for field in (
        "schema_version",
        "generated_at",
        "status",
        "sample_count",
        "minimum_samples",
        "objectives",
        "reasons",
    ):
        if field not in report:
            errors.append(f"recovery alert delivery SLO report missing field {field}")
    if report.get("schema_version") != 1:
        errors.append("recovery alert delivery SLO schema version must be 1")
    if report.get("status") not in {"PASS", "WARN", "FAIL", "INSUFFICIENT_DATA"}:
        errors.append("recovery alert delivery SLO status is invalid")
    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    errors = list(verify_configuration())
    if args.report is not None:
        errors.extend(verify_report(args.report))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(
        "recovery alert delivery SLO policy verified"
        if args.report is None
        else f"recovery alert delivery SLO verified: {args.report}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
