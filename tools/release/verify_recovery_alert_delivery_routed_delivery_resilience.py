"""Verify routed recovery alert delivery resilience policy."""

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
        "max_attempts": 4,
        "initial_backoff_seconds": 1,
        "backoff_multiplier": 2,
        "max_backoff_seconds": 8,
        "retry_server_errors": True,
        "retry_status_codes": [408, 425, 429],
        "retry_transport_errors": True,
        "preserve_route_across_retries": True,
        "preserve_delivery_id_across_retries": True,
    }
    if alerting.get("routed_delivery_resilience") != expected:
        errors.append("routed recovery alert delivery resilience policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "--policy release/recovery-alerting.toml",
        "verify_recovery_alert_delivery_routed_delivery_resilience.py",
        "Verify routed recovery alert delivery resilience",
    ):
        if fragment not in workflow:
            errors.append(f"routed delivery resilience workflow missing {fragment}")

    forbidden = (
        "RECOVERY_ROUTED_WEBHOOK_URL",
        "RECOVERY_ROUTED_HMAC_SECRET",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"routed delivery resilience workflow contains {fragment}")

    return tuple(errors)


def verify_receipt(receipt: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []

    if receipt.get("schema_version") != 2:
        errors.append("routed delivery receipt schema_version must be 2")

    attempts = receipt.get("attempts")
    history = receipt.get("attempt_history")
    if not isinstance(attempts, int) or attempts < 0:
        errors.append("routed delivery receipt attempts must be non-negative")
    if not isinstance(history, list):
        errors.append("routed delivery receipt attempt_history must be a list")
        return tuple(errors)

    if isinstance(attempts, int) and attempts != len(history):
        errors.append("routed delivery attempts must match attempt_history length")

    expected_attempt = 1
    for item in history:
        if not isinstance(item, dict):
            errors.append("routed delivery attempt history items must be objects")
            continue
        if item.get("attempt") != expected_attempt:
            errors.append("routed delivery attempt history must be sequential")
        expected_attempt += 1

    if receipt.get("route_required") and not receipt.get("delivery_id"):
        errors.append("required routed delivery must preserve a delivery_id")

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
            errors.append(f"unable to load routed delivery receipt: {exc}")
        else:
            if not isinstance(data, dict):
                errors.append("routed delivery receipt must be a JSON object")
            else:
                errors.extend(verify_receipt(data))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert routed delivery resilience policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
