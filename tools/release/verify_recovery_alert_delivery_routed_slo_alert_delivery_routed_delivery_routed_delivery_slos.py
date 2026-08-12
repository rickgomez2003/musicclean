from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_FRAGMENTS = (
    "endpoint_url",
    "hmac_secret",
    "signature",
    "authorization",
    "webhook_url",
    "request_headers",
    "https://",
    "http://",
)


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    with (root / "release/recovery-alerting.toml").open("rb") as stream:
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        return ("recovery alerting policy is missing",)

    expected = {
        "schema_version": 1,
        "minimum_samples": 3,
        "delivery_success_rate_pass": 0.99,
        "delivery_success_rate_warn": 0.97,
        "retry_rate_pass": 0.10,
        "retry_rate_warn": 0.25,
        "average_attempts_pass": 1.10,
        "average_attempts_warn": 1.50,
        "transport_failure_rate_pass": 0.01,
        "transport_failure_rate_warn": 0.05,
        "external_export_enabled": False,
        "provider_neutral": True,
    }

    if alerting.get("routed_slo_alert_delivery_routed_delivery_routed_delivery_slos") != expected:
        errors.append("routed-delivery SLO policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    for fragment in (
        "Evaluate routed recovery SLO alert delivery routed delivery routed delivery SLOs",
        "Verify routed recovery SLO alert delivery routed delivery routed delivery SLOs",
        "evaluate_recovery_alert_routed_slo_delivery_routed_delivery_routed_delivery_slos.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_routed_delivery_slos.py",
        "recovery-alert-routed-slo-delivery-routed-delivery-slos.json",
        "recovery-alert-routed-slo-delivery-routed-delivery-slos-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"workflow missing {fragment}")

    return tuple(errors)


def verify_report(report: Any) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(report, dict):
        return ("routed-delivery SLO evidence must be a JSON object",)

    if report.get("schema_version") != 1:
        errors.append("SLO schema_version must be 1")

    if report.get("overall_status") not in {
        "PASS",
        "WARN",
        "FAIL",
        "INSUFFICIENT_SAMPLES",
    }:
        errors.append("SLO overall_status is invalid")

    sample_count = report.get("sample_count")
    minimum_samples = report.get("minimum_samples")
    authoritative = report.get("authoritative")

    if not isinstance(sample_count, int) or sample_count < 0:
        errors.append("sample_count must be a non-negative integer")

    if not isinstance(minimum_samples, int) or minimum_samples < 1:
        errors.append("minimum_samples must be a positive integer")

    if not isinstance(authoritative, bool):
        errors.append("authoritative must be a boolean")

    if (
        isinstance(sample_count, int)
        and isinstance(minimum_samples, int)
        and sample_count < minimum_samples
    ):
        if report.get("overall_status") != "INSUFFICIENT_SAMPLES":
            errors.append("insufficient samples must produce INSUFFICIENT_SAMPLES")
        if authoritative is not False:
            errors.append("insufficient samples must be non-authoritative")

    metrics = report.get("metrics")
    if not isinstance(metrics, dict):
        errors.append("metrics must be an object")
    else:
        expected_metrics = {
            "delivery_success_rate",
            "retry_rate",
            "average_attempts",
            "transport_failure_rate",
        }
        if set(metrics) != expected_metrics:
            errors.append("metrics set is invalid")

    if report.get("external_export_enabled") is not False:
        errors.append("external export must remain disabled")

    if report.get("provider_neutral") is not True:
        errors.append("SLO evidence must remain provider-neutral")

    serialized = json.dumps(report, sort_keys=True).lower()
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment in serialized:
            errors.append(f"SLO evidence contains forbidden material {fragment}")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())
    if args.report is not None:
        errors.extend(verify_report(json.loads(args.report.read_text(encoding="utf-8"))))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        "recovery alert routed SLO alert delivery routed delivery "
        "routed delivery SLO policy verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
