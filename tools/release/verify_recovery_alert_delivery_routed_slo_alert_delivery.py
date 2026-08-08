"""Verify routed recovery SLO alert delivery policy and workflow."""

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
        "https_required": True,
        "signature_algorithm": "hmac-sha256",
        "operations_secret_prefix": "RECOVERY_SLO_ALERT_OPERATIONS_",
        "incident_secret_prefix": "RECOVERY_SLO_ALERT_INCIDENT_",
    }

    if alerting.get("routed_slo_alert_delivery") != expected:
        errors.append("routed recovery SLO alert delivery policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    for fragment in (
        "Deliver routed recovery SLO alert",
        "Verify routed recovery SLO alert delivery",
        "deliver_routed_recovery_slo_alert.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery.py",
        "RECOVERY_SLO_ALERT_OPERATIONS_WEBHOOK_URL",
        "RECOVERY_SLO_ALERT_OPERATIONS_HMAC_SECRET",
        "RECOVERY_SLO_ALERT_INCIDENT_WEBHOOK_URL",
        "RECOVERY_SLO_ALERT_INCIDENT_HMAC_SECRET",
        "recovery-alert-routed-slo-delivery.json",
    ):
        if fragment not in workflow:
            errors.append(f"routed SLO alert delivery workflow missing {fragment}")

    if "GITHUB_ENV" in workflow:
        errors.append("routed SLO alert delivery must not persist credentials through GITHUB_ENV")

    for forbidden in (
        "contents: write",
        "actions: write",
        "packages: write",
        "pull-requests: write",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    ):
        if forbidden in workflow:
            errors.append(f"routed SLO alert delivery workflow contains {forbidden}")

    return tuple(errors)


def verify_receipt(receipt: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []

    if receipt.get("schema_version") != 1:
        errors.append("routed SLO alert delivery receipt schema_version must be 1")

    if receipt.get("route") not in {
        "none",
        "operations",
        "incident-response",
    }:
        errors.append("routed SLO alert delivery receipt route is invalid")

    if receipt.get("status") not in {
        "NOT_REQUIRED",
        "DELIVERED",
        "FAILED",
    }:
        errors.append("routed SLO alert delivery receipt status is invalid")

    serialized = json.dumps(receipt, sort_keys=True).lower()
    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
    ):
        if fragment in serialized:
            errors.append(
                f"routed SLO alert delivery receipt contains forbidden field/material {fragment}"
            )

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    if args.receipt is not None:
        try:
            data = json.loads(args.receipt.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"unable to load routed SLO alert delivery receipt: {exc}")
        else:
            if not isinstance(data, dict):
                errors.append("routed SLO alert delivery receipt must be a JSON object")
            else:
                errors.extend(verify_receipt(data))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert routed SLO alert delivery policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
