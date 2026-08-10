"""Verify routed recovery SLO alert-delivery routed-delivery policy."""

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
        "operations_secret_prefix": "RECOVERY_SLO_DELIVERY_OPERATIONS_",
        "incident_secret_prefix": "RECOVERY_SLO_DELIVERY_INCIDENT_",
        "timeout_seconds": 10.0,
    }

    if alerting.get("routed_slo_alert_delivery_routed_delivery") != expected:
        errors.append("routed SLO alert delivery routed-delivery policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    required = (
        "Deliver routed recovery SLO alert delivery",
        "Verify routed recovery SLO alert delivery routed delivery",
        "deliver_routed_recovery_slo_delivery_alert.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery.py",
        "RECOVERY_SLO_DELIVERY_OPERATIONS_WEBHOOK_URL",
        "RECOVERY_SLO_DELIVERY_OPERATIONS_HMAC_SECRET",
        "RECOVERY_SLO_DELIVERY_INCIDENT_WEBHOOK_URL",
        "RECOVERY_SLO_DELIVERY_INCIDENT_HMAC_SECRET",
        "recovery-alert-routed-slo-delivery-routed-delivery.json",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"routed SLO alert delivery workflow missing {fragment}")

    forbidden = (
        "GITHUB_ENV",
        "contents: write",
        "actions: write",
        "packages: write",
        "pull-requests: write",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "http://",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"workflow contains forbidden material {fragment}")

    return tuple(errors)


def verify_receipt(receipt: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []

    if receipt.get("schema_version") != 1:
        errors.append("routed-delivery receipt schema_version must be 1")

    if receipt.get("logical_route") not in {
        "none",
        "operations",
        "incident-response",
    }:
        errors.append("routed-delivery receipt logical_route is invalid")

    if not isinstance(receipt.get("delivery_id"), str):
        errors.append("routed-delivery receipt delivery_id is required")

    serialized = json.dumps(receipt, sort_keys=True).lower()
    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
        "request_headers",
    ):
        if fragment in serialized:
            errors.append(f"routed-delivery receipt contains forbidden material {fragment}")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    if args.receipt is not None:
        data = json.loads(args.receipt.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            errors.append("routed-delivery receipt must be a JSON object")
        else:
            errors.extend(verify_receipt(data))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert routed SLO alert delivery routed delivery policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
