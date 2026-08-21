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
    "webhook_url",
    "hmac_secret",
    "signature",
    "authorization",
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
        "https_only": True,
        "hmac_sha256": True,
        "deterministic_delivery_id": True,
        "route_specific_credentials": True,
        "persist_endpoint_urls": False,
        "persist_credentials": False,
        "persist_request_headers": False,
        "secret_safe_receipts": True,
    }

    key = "routed_slo_alert_delivery_routed_delivery_routed_delivery_routed_delivery"
    if alerting.get(key) != expected:
        errors.append("routed-delivery delivery policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    fragments = (
        (
            "Deliver routed recovery SLO alert delivery routed delivery "
            "routed delivery routed delivery"
        ),
        (
            "Verify routed recovery SLO alert delivery routed delivery "
            "routed delivery routed delivery"
        ),
        ("deliver_routed_recovery_slo_delivery_routed_delivery_routed_delivery_alert.py"),
        (
            "verify_recovery_alert_delivery_routed_slo_alert_delivery_"
            "routed_delivery_routed_delivery_routed_delivery.py"
        ),
        ("recovery-alert-routed-slo-delivery-routed-delivery-routed-delivery.json"),
    )

    for fragment in fragments:
        if fragment not in workflow:
            errors.append(f"workflow missing {fragment}")

    return tuple(errors)


def verify_receipt(receipt: Any) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(receipt, dict):
        return ("delivery receipt must be a JSON object",)

    if receipt.get("schema_version") != 1:
        errors.append("receipt schema_version must be 1")

    route = receipt.get("logical_route")
    if route not in {
        "none",
        "operations",
        "incident_response",
    }:
        errors.append("logical_route is invalid")

    if not isinstance(receipt.get("delivery_attempted"), bool):
        errors.append("delivery_attempted must be boolean")

    if not isinstance(receipt.get("delivered"), bool):
        errors.append("delivered must be boolean")

    if route == "none" and receipt.get("delivery_attempted") is not False:
        errors.append("none route must not attempt delivery")

    if receipt.get("provider_neutral") is not True:
        errors.append("delivery receipt must remain provider-neutral")

    delivery_id = receipt.get("delivery_id")
    if delivery_id is not None and (not isinstance(delivery_id, str) or len(delivery_id) != 64):
        errors.append("delivery_id must be a SHA-256 hex digest")

    serialized = json.dumps(receipt, sort_keys=True).lower()
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment in serialized:
            errors.append(f"receipt contains forbidden material {fragment}")

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
        "recovery alert routed SLO alert delivery routed delivery "
        "routed delivery routed delivery policy verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
