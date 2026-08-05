"""Verify external recovery alert delivery policy and workflow integration."""

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
    if not isinstance(delivery, dict):
        errors.append("external recovery alert delivery policy is missing")
    else:
        expected = {
            "environment": "release-archive-export",
            "url_secret": "RECOVERY_ALERT_WEBHOOK_URL",
            "hmac_secret": "RECOVERY_ALERT_WEBHOOK_HMAC_SECRET",
            "request_timeout_seconds": 10,
            "max_attempts": 3,
            "require_https": True,
            "sign_payload": True,
        }
        if delivery != expected:
            errors.append("external recovery alert delivery policy is invalid")

    workflow = (root / ".github" / "workflows" / "orion-recovery-drill.yml").read_text(
        encoding="utf-8"
    )

    required = (
        "actions: read",
        "contents: read",
        "id-token: write",
        "environment:",
        "Deliver external recovery alert",
        "deliver_recovery_alert.py",
        "RECOVERY_ALERT_WEBHOOK_URL",
        "RECOVERY_ALERT_WEBHOOK_HMAC_SECRET",
        "recovery-alert-delivery.json",
        "Verify external recovery alert delivery",
        "verify_external_recovery_alert_delivery.py",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"recovery workflow missing delivery integration {fragment}")

    ordered = (
        "Verify recovery SLO alert",
        "Publish recovery SLO summary",
        "Deliver external recovery alert",
        "Verify external recovery alert delivery",
        "Upload recovery drill evidence",
    )
    positions = [workflow.find(step) for step in ordered]
    if any(position == -1 for position in positions):
        errors.append("external alert workflow ordering cannot be verified")
    elif positions != sorted(positions):
        errors.append("external alert workflow ordering is invalid")

    forbidden = (
        "contents: write",
        "issues: write",
        "pull-requests: write",
        "gh release edit",
        "gh release create",
        "gh release upload",
        "git tag",
        "git push",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "--admin",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"external alert workflow contains forbidden pattern {fragment}")

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
        "status_code",
        "provider",
        "severity",
        "reason",
    )
    for field in required:
        if field not in receipt:
            errors.append(f"external alert delivery receipt missing field {field}")

    if receipt.get("schema_version") != 1:
        errors.append("external alert delivery receipt schema version must be 1")
    if receipt.get("provider") != "generic-webhook":
        errors.append("external alert delivery receipt provider is invalid")
    if receipt.get("delivery_required") is False and receipt.get("attempts") != 0:
        errors.append("non-required alert delivery must not make attempts")

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
