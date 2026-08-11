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
        "max_attempt_records": 3,
        "external_export_enabled": False,
        "provider_neutral": True,
        "secret_safe": True,
    }

    if (
        alerting.get("routed_slo_alert_delivery_routed_delivery_routed_delivery_observability")
        != expected
    ):
        errors.append("routed-delivery observability policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    for fragment in (
        "Build routed recovery SLO alert delivery routed delivery routed delivery observability",
        "Verify routed recovery SLO alert delivery routed delivery routed delivery observability",
        "build_recovery_alert_routed_slo_delivery_routed_delivery_routed_delivery_observability.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_routed_delivery_observability.py",
        "recovery-alert-routed-slo-delivery-routed-delivery-observability.json",
    ):
        if fragment not in workflow:
            errors.append(f"workflow missing {fragment}")

    return tuple(errors)


def verify_report(report: Any) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(report, dict):
        return ("observability evidence must be a JSON object",)

    if report.get("schema_version") != 1:
        errors.append("observability schema_version must be 1")

    if report.get("logical_route") not in {
        "none",
        "operations",
        "incident-response",
    }:
        errors.append("observability logical_route is invalid")

    if report.get("delivery_status") not in {
        "NOT_REQUIRED",
        "DELIVERED",
        "FAILED",
    }:
        errors.append("observability delivery_status is invalid")

    if not isinstance(report.get("attempt_count"), int):
        errors.append("attempt_count must be an integer")

    if not isinstance(report.get("retry_count"), int):
        errors.append("retry_count must be an integer")

    attempts = report.get("attempts")
    if not isinstance(attempts, list):
        errors.append("attempts must be a list")
    elif len(attempts) > 3:
        errors.append("attempt evidence exceeds configured bound")

    if report.get("external_export_enabled") is not False:
        errors.append("external export must remain disabled")

    serialized = json.dumps(report, sort_keys=True).lower()
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment in serialized:
            errors.append(f"observability evidence contains forbidden material {fragment}")

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
        "routed delivery observability policy verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
