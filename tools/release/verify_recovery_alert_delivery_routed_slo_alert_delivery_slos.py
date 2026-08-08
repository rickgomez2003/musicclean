"""Verify routed SLO alert delivery SLO policy and evidence."""

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
        "minimum_samples": 5,
        "sample_count": 5,
        "success_rate_warn": 0.99,
        "success_rate_fail": 0.95,
        "retry_rate_warn": 0.10,
        "retry_rate_fail": 0.25,
        "average_attempts_warn": 1.25,
        "average_attempts_fail": 2.0,
        "transport_failure_rate_warn": 0.02,
        "transport_failure_rate_fail": 0.05,
    }

    if alerting.get("routed_slo_alert_delivery_slos") != expected:
        errors.append("routed SLO alert delivery SLO policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    for fragment in (
        "Evaluate routed recovery SLO alert delivery SLOs",
        "Verify routed recovery SLO alert delivery SLOs",
        "Publish routed recovery SLO alert delivery SLO summary",
        "evaluate_recovery_alert_routed_slo_delivery_slos.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_slos.py",
        "recovery-alert-routed-slo-delivery-slos.json",
        "recovery-alert-routed-slo-delivery-slos-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"routed SLO alert delivery SLO workflow missing {fragment}")

    return tuple(errors)


def verify_report(report: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []

    if report.get("schema_version") != 1:
        errors.append("routed SLO alert delivery SLO schema_version must be 1")

    if report.get("status") not in {
        "PASS",
        "WARN",
        "FAIL",
        "INSUFFICIENT_SAMPLES",
    }:
        errors.append("routed SLO alert delivery SLO status is invalid")

    if not isinstance(report.get("metrics"), list):
        errors.append("routed SLO alert delivery SLO metrics must be a list")

    serialized = json.dumps(report, sort_keys=True).lower()
    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
        "request_headers",
    ):
        if fragment in serialized:
            errors.append(
                f"routed SLO alert delivery SLO evidence contains forbidden material {fragment}"
            )

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    if args.report is not None:
        data = json.loads(args.report.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            errors.append("routed SLO alert delivery SLO report must be a JSON object")
        else:
            errors.extend(verify_report(data))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert routed SLO alert delivery SLO policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
