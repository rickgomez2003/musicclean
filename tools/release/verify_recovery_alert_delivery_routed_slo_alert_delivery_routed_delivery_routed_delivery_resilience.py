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
        "max_attempts": 3,
        "initial_backoff_seconds": 1.0,
        "max_backoff_seconds": 4.0,
        "retry_transport_errors": True,
        "retry_http_statuses": [408, 425, 429, 500, 502, 503, 504],
        "preserve_delivery_id": True,
        "max_attempt_records": 3,
    }

    if (
        alerting.get("routed_slo_alert_delivery_routed_delivery_routed_delivery_resilience")
        != expected
    ):
        errors.append("routed-delivery resilience policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "Verify routed recovery SLO alert delivery routed delivery routed delivery resilience",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_routed_delivery_resilience.py",
        "recovery-alert-routed-slo-delivery-routed-delivery-delivery.json",
    ):
        if fragment not in workflow:
            errors.append(f"routed-delivery resilience workflow missing {fragment}")

    return tuple(errors)


def verify_receipt(receipt: Any) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(receipt, dict):
        return ("routed-delivery resilience receipt must be a JSON object",)

    if receipt.get("schema_version") != 2:
        errors.append("receipt schema_version must be 2")

    if receipt.get("logical_route") not in {"none", "operations", "incident-response"}:
        errors.append("receipt logical_route is invalid")

    if receipt.get("delivery_status") not in {"NOT_REQUIRED", "DELIVERED", "FAILED"}:
        errors.append("receipt delivery_status is invalid")

    delivery_id = receipt.get("delivery_id")
    if (
        not isinstance(delivery_id, str)
        or len(delivery_id) != 64
        or any(ch not in "0123456789abcdef" for ch in delivery_id)
    ):
        errors.append("receipt delivery_id must be a SHA-256 hex digest")

    attempt_count = receipt.get("attempt_count")
    retry_count = receipt.get("retry_count")
    attempts = receipt.get("attempts")

    if not isinstance(attempt_count, int) or attempt_count < 0:
        errors.append("attempt_count must be a non-negative integer")
    if not isinstance(retry_count, int) or retry_count < 0:
        errors.append("retry_count must be a non-negative integer")
    if (
        isinstance(attempt_count, int)
        and isinstance(retry_count, int)
        and retry_count != max(0, attempt_count - 1)
    ):
        errors.append("retry_count must equal attempt_count - 1")

    if not isinstance(attempts, list):
        errors.append("attempts must be a list")
    elif (
        isinstance(attempt_count, int)
        and receipt.get("logical_route") != "none"
        and len(attempts) != attempt_count
    ):
        errors.append("attempt record count must match attempt_count")

    if isinstance(attempts, list) and len(attempts) > 3:
        errors.append("attempt evidence exceeds configured bound")

    if receipt.get("logical_route") == "none":
        if receipt.get("delivery_status") != "NOT_REQUIRED":
            errors.append("none route must not perform delivery")
        if attempt_count != 0 or retry_count != 0:
            errors.append("none route must have zero attempts and retries")

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
        "routed delivery resilience policy verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
