"""Verify routed SLO alert delivery routed-delivery observability policy."""

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
        "max_attempt_records": 10,
        "retain_days": 90,
        "external_export_enabled": False,
    }

    if alerting.get("routed_slo_alert_delivery_routed_delivery_observability") != expected:
        errors.append("routed SLO alert delivery routed-delivery observability policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    for fragment in (
        "Build routed recovery SLO alert delivery routed delivery observability",
        "Verify routed recovery SLO alert delivery routed delivery observability",
        "build_recovery_alert_routed_slo_delivery_routed_delivery_observability.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_observability.py",
        "recovery-alert-routed-slo-delivery-routed-delivery-observability.json",
        "recovery-alert-routed-slo-delivery-routed-delivery-observability-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"observability workflow missing {fragment}")

    return tuple(errors)


def verify_report(report: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []

    if report.get("schema_version") != 1:
        errors.append("observability schema_version must be 1")

    if report.get("logical_route") not in {
        "none",
        "operations",
        "incident-response",
    }:
        errors.append("observability logical_route is invalid")

    if not isinstance(report.get("delivery_id"), str):
        errors.append("observability delivery_id is required")

    if not isinstance(report.get("attempt_count"), int):
        errors.append("observability attempt_count must be an integer")

    if not isinstance(report.get("retry_count"), int):
        errors.append("observability retry_count must be an integer")

    attempts = report.get("attempts")
    if not isinstance(attempts, list):
        errors.append("observability attempts must be a list")
    elif len(attempts) > 10:
        errors.append("observability attempt evidence exceeds configured bound")

    if report.get("external_export_enabled") is not False:
        errors.append("observability external export must remain disabled")

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
            errors.append(f"observability contains forbidden material {fragment}")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    if args.report is not None:
        data = json.loads(args.report.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            errors.append("observability report must be a JSON object")
        else:
            errors.extend(verify_report(data))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert routed SLO alert delivery routed delivery observability policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
