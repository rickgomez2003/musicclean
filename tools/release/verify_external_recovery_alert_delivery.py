"""Verify external recovery alert delivery policy and integration."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    policy_path = root / "release" / "recovery-alerting.toml"
    try:
        with policy_path.open("rb") as stream:
            document = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return (f"unable to load recovery alerting policy: {exc}",)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        return ("recovery alerting policy is missing",)

    if alerting.get("provider") != "generic-webhook":
        errors.append("external recovery alert provider must be generic-webhook")
    if alerting.get("external_delivery_enabled") is not True:
        errors.append("external recovery alert delivery must be enabled")

    delivery = alerting.get("delivery")
    expected = {
        "environment": "recovery-alert-delivery",
        "url_secret": "RECOVERY_ALERT_WEBHOOK_URL",
        "hmac_secret": "RECOVERY_ALERT_WEBHOOK_HMAC_SECRET",
        "request_timeout_seconds": 10,
        "max_attempts": 4,
        "initial_backoff_seconds": 1,
        "maximum_backoff_seconds": 8,
        "retry_statuses": [408, 429],
        "retry_server_errors": True,
        "require_https": True,
        "sign_payload": True,
        "idempotency_header": "X-MusicClean-Delivery-ID",
        "signature_header": "X-MusicClean-Signature-SHA256",
    }
    if delivery != expected:
        errors.append("external recovery alert delivery policy is invalid")

    workflow = (
        root / ".github" / "workflows" / "orion-recovery-drill.yml"
    ).read_text(encoding="utf-8")

    required = (
        "recovery-alert-delivery",
        "needs: recovery-drill",
        "actions: read",
        "contents: read",
        "Deliver external recovery alert",
        "actions/download-artifact@v4",
        "RECOVERY_ALERT_WEBHOOK_URL",
        "RECOVERY_ALERT_WEBHOOK_HMAC_SECRET",
        "recovery-alert-delivery.json",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"recovery workflow missing delivery integration {fragment}")

    delivery_job = workflow.split("  external-alert-delivery:", 1)
    if len(delivery_job) != 2:
        errors.append("external recovery alert delivery job is missing")
    else:
        body = delivery_job[1]
        if "id-token: write" in body:
            errors.append("external alert delivery job must not have OIDC write permission")
        if "name: release-archive-export" in body:
            errors.append("external alert delivery job must not use archive environment")
        if "name: recovery-alert-delivery" not in body:
            errors.append(
                "external alert delivery job must use "
                "recovery-alert-delivery environment"
            )

    return tuple(errors)


def verify_receipt(path: Path) -> tuple[str, ...]:
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load external alert delivery receipt: {exc}",)

    if not isinstance(receipt, dict):
        return ("external alert delivery receipt must be an object",)

    errors: list[str] = []
    required = (
        "schema_version",
        "delivered_at",
        "delivery_required",
        "delivered",
        "attempts",
        "attempt_history",
        "status_code",
        "provider",
        "severity",
        "delivery_id",
        "failure_class",
        "reason",
    )
    for field in required:
        if field not in receipt:
            errors.append(f"external alert delivery receipt missing field {field}")

    if receipt.get("schema_version") != 2:
        errors.append("external alert delivery receipt schema version must be 2")
    if receipt.get("provider") != "generic-webhook":
        errors.append("external alert delivery receipt provider is invalid")

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

    if args.receipt is None:
        print("external recovery alert delivery policy verified")
    else:
        print(f"external recovery alert delivery verified: {args.receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
