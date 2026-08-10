"""Verify routed recovery SLO alert-delivery routed-delivery resilience."""

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
        "base_delay_seconds": 1.0,
        "max_delay_seconds": 4.0,
        "retryable_http_statuses": [408, 425, 429, 500, 502, 503, 504],
        "retry_transport_errors": True,
        "preserve_delivery_id": True,
    }

    if alerting.get("routed_slo_alert_delivery_routed_delivery_resilience") != expected:
        errors.append("routed SLO alert delivery routed-delivery resilience policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "--policy release/recovery-alerting.toml",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_resilience.py",
    ):
        if fragment not in workflow:
            errors.append(f"routed-delivery resilience workflow missing {fragment}")

    return tuple(errors)


def verify_receipt(receipt: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []

    if receipt.get("schema_version") != 1:
        errors.append("resilient routed-delivery receipt schema_version must be 1")

    attempt_count = receipt.get("attempt_count")
    retry_count = receipt.get("retry_count")
    attempts = receipt.get("attempts")

    if not isinstance(attempt_count, int) or attempt_count < 0:
        errors.append("attempt_count must be a non-negative integer")
    if not isinstance(retry_count, int) or retry_count < 0:
        errors.append("retry_count must be a non-negative integer")
    if not isinstance(attempts, list):
        errors.append("attempts must be a list")
    elif (
        isinstance(attempt_count, int)
        and len(attempts) != attempt_count
        and receipt.get("logical_route") != "none"
    ):
        errors.append("attempt record count must match attempt_count")

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
            errors.append(f"resilient receipt contains forbidden material {fragment}")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    if args.receipt is not None:
        data = json.loads(args.receipt.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            errors.append("resilient routed-delivery receipt must be a JSON object")
        else:
            errors.extend(verify_receipt(data))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert routed SLO alert delivery routed delivery resilience policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
