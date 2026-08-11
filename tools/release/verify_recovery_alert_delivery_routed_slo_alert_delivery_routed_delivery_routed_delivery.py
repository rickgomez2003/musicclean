"""Verify routed SLO alert-delivery routed-delivery delivery policy/evidence."""

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
        "operations_route": "operations",
        "incident_route": "incident-response",
        "none_route": "none",
        "https_only": True,
        "signature_algorithm": "hmac-sha256",
        "deterministic_delivery_id": True,
        "external_delivery_enabled": True,
    }

    if alerting.get("routed_slo_alert_delivery_routed_delivery_routed_delivery") != expected:
        errors.append("routed SLO alert-delivery routed-delivery delivery policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    for fragment in (
        "Deliver routed recovery SLO alert delivery routed delivery",
        "Verify routed recovery SLO alert delivery routed delivery routed delivery",
        "deliver_routed_recovery_slo_delivery_routed_delivery_alert.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_routed_delivery.py",
        "recovery-alert-routed-slo-delivery-routed-delivery-delivery.json",
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_OPERATIONS_URL",
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_OPERATIONS_HMAC_SECRET",
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_INCIDENT_URL",
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_INCIDENT_HMAC_SECRET",
    ):
        if fragment not in workflow:
            errors.append(f"routed-delivery workflow missing {fragment}")

    forbidden = (
        "GITHUB_ENV",
        "contents: write",
        "actions: write",
        "packages: write",
        "pull-requests: write",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"routed-delivery workflow contains forbidden material {fragment}")

    return tuple(errors)


def verify_receipt(receipt: Any) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(receipt, dict):
        return ("routed-delivery receipt must be a JSON object",)

    if receipt.get("schema_version") != 1:
        errors.append("receipt schema_version must be 1")

    if receipt.get("logical_route") not in {
        "none",
        "operations",
        "incident-response",
    }:
        errors.append("receipt logical_route is invalid")

    if receipt.get("delivery_status") not in {
        "NOT_REQUIRED",
        "DELIVERED",
        "FAILED",
    }:
        errors.append("receipt delivery_status is invalid")

    delivery_id = receipt.get("delivery_id")
    if (
        not isinstance(delivery_id, str)
        or len(delivery_id) != 64
        or any(ch not in "0123456789abcdef" for ch in delivery_id)
    ):
        errors.append("receipt delivery_id must be a SHA-256 hex digest")

    if receipt.get("logical_route") == "none" and receipt.get("delivery_status") != "NOT_REQUIRED":
        errors.append("none route must not perform delivery")

    serialized = json.dumps(receipt, sort_keys=True).lower()
    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
        "request_headers",
        "https://",
        "http://",
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
        errors.extend(verify_receipt(json.loads(args.receipt.read_text(encoding="utf-8"))))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        "recovery alert routed SLO alert delivery routed delivery routed delivery policy verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
