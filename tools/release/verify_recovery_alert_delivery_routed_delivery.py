"""Verify routed recovery alert delivery policy and receipt."""

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
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        return ("recovery alerting policy is missing",)

    expected = {
        "schema_version": 1,
        "operations_url_secret": "RECOVERY_ALERT_OPERATIONS_WEBHOOK_URL",
        "operations_hmac_secret": "RECOVERY_ALERT_OPERATIONS_HMAC_SECRET",
        "incident_url_secret": "RECOVERY_ALERT_INCIDENT_WEBHOOK_URL",
        "incident_hmac_secret": "RECOVERY_ALERT_INCIDENT_HMAC_SECRET",
        "timeout_seconds": 10,
        "require_https": True,
        "signed_payloads": True,
    }
    if alerting.get("routed_delivery") != expected:
        errors.append("routed recovery alert delivery policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "Deliver routed recovery alert",
        "Verify routed recovery alert delivery",
        "deliver_routed_recovery_alert.py",
        "verify_recovery_alert_delivery_routed_delivery.py",
        "RECOVERY_ALERT_OPERATIONS_WEBHOOK_URL",
        "RECOVERY_ALERT_OPERATIONS_HMAC_SECRET",
        "RECOVERY_ALERT_INCIDENT_WEBHOOK_URL",
        "RECOVERY_ALERT_INCIDENT_HMAC_SECRET",
        "recovery-alert-routed-delivery.json",
    ):
        if fragment not in workflow:
            errors.append(f"routed recovery alert workflow missing {fragment}")

    # Security invariant: routed credentials must remain scoped to the
    # delivery step and must never be persisted through GITHUB_ENV.
    if "GITHUB_ENV" in workflow:
        errors.append(
            "routed recovery alert workflow must not persist "
            "delivery credentials through GITHUB_ENV"
        )

    if "RECOVERY_ROUTED_WEBHOOK_URL" in workflow:
        errors.append("routed recovery alert workflow must not persist a routed webhook URL")

    if "RECOVERY_ROUTED_HMAC_SECRET" in workflow:
        errors.append("routed recovery alert workflow must not persist a routed HMAC secret")

    forbidden = (
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
            errors.append(f"routed recovery alert workflow contains forbidden {fragment}")

    return tuple(errors)


def verify_receipt(path: Path) -> tuple[str, ...]:
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load routed delivery receipt: {exc}",)

    if not isinstance(receipt, dict):
        return ("routed delivery receipt must be a JSON object",)

    errors: list[str] = []
    for field in (
        "schema_version",
        "delivered_at",
        "elapsed_seconds",
        "route_required",
        "delivered",
        "route",
        "severity",
        "status_code",
        "delivery_id",
        "failure_class",
    ):
        if field not in receipt:
            errors.append(f"routed delivery receipt missing field {field}")

    elapsed = receipt.get("elapsed_seconds")
    if not isinstance(elapsed, (int, float)) or elapsed < 0:
        errors.append("routed delivery elapsed_seconds must be non-negative")

    if receipt.get("route_required") and receipt.get("route") == "none":
        errors.append("required routed delivery cannot target route none")

    if receipt.get("delivered") and receipt.get("status_code") not in range(200, 300):
        errors.append("successful routed delivery must have 2xx status")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())
    if args.receipt is not None:
        errors.extend(verify_receipt(args.receipt))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert routed delivery policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
