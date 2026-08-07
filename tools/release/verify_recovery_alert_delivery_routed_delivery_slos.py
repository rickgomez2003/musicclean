"""Verify routed recovery alert delivery SLO policy and reports."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

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
        "minimum_samples": 4,
        "success_rate": {
            "warn_below": 0.98,
            "fail_below": 0.95,
        },
        "retry_rate": {
            "warn_above": 0.20,
            "fail_above": 0.35,
        },
        "average_attempts": {
            "warn_above": 1.50,
            "fail_above": 2.00,
        },
        "average_latency_seconds": {
            "warn_above": 5.0,
            "fail_above": 10.0,
        },
        "terminal_http_failure_rate": {
            "warn_above": 0.02,
            "fail_above": 0.05,
        },
        "transport_failure_rate": {
            "warn_above": 0.02,
            "fail_above": 0.05,
        },
    }

    if alerting.get("routed_delivery_slos") != expected:
        errors.append("routed recovery alert delivery SLO policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    for fragment in (
        "Evaluate routed recovery alert delivery SLOs",
        "Verify routed recovery alert delivery SLOs",
        "Publish routed recovery alert delivery SLO summary",
        "evaluate_recovery_alert_routed_delivery_slos.py",
        "verify_recovery_alert_delivery_routed_delivery_slos.py",
        "recovery-alert-routed-delivery-slo.json",
        "recovery-alert-routed-delivery-slo-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"routed delivery SLO workflow missing {fragment}")

    return tuple(errors)


def verify_report(report: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []

    required = (
        "schema_version",
        "generated_at",
        "sample_count",
        "minimum_samples",
        "authoritative",
        "sample_gate",
        "status",
        "evaluations",
        "current_route",
        "current_severity",
    )
    for field in required:
        if field not in report:
            errors.append(f"routed delivery SLO report missing field {field}")

    if report.get("schema_version") != 1:
        errors.append("routed delivery SLO report schema_version must be 1")

    if report.get("status") not in {"PASS", "WARN", "FAIL"}:
        errors.append("routed delivery SLO status is invalid")

    if report.get("sample_gate") not in {
        "READY",
        "INSUFFICIENT_SAMPLES",
    }:
        errors.append("routed delivery SLO sample_gate is invalid")

    evaluations = report.get("evaluations")
    if not isinstance(evaluations, list) or len(evaluations) != 6:
        errors.append("routed delivery SLO report must contain six evaluations")
    else:
        for item in evaluations:
            if not isinstance(item, dict):
                errors.append("routed delivery SLO evaluations must be objects")
                continue
            if item.get("status") not in {"PASS", "WARN", "FAIL"}:
                errors.append("routed delivery SLO evaluation status is invalid")

    serialized = json.dumps(report, sort_keys=True).lower()
    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
    ):
        if fragment in serialized:
            errors.append(
                f"routed delivery SLO report contains forbidden field/material {fragment}"
            )

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    if args.report is not None:
        try:
            data = json.loads(args.report.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"unable to load routed delivery SLO report: {exc}")
        else:
            if not isinstance(data, dict):
                errors.append("routed delivery SLO report must be a JSON object")
            else:
                errors.extend(verify_report(data))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert routed delivery SLO policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
