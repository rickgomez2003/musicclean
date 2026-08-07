"""Verify routed recovery alert delivery observability policy and artifacts."""

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
        "history_limit": 52,
        "record_success_rate": True,
        "record_retry_rate": True,
        "record_attempt_distribution": True,
        "record_route_distribution": True,
        "record_failure_classes": True,
        "record_latency": True,
        "record_destination": False,
        "record_secret_material": False,
    }
    if alerting.get("routed_delivery_observability") != expected:
        errors.append("routed recovery alert delivery observability policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "Build routed recovery alert delivery observability",
        "Verify routed recovery alert delivery observability",
        "Publish routed recovery alert delivery observability summary",
        "build_recovery_alert_routed_delivery_observability.py",
        "verify_recovery_alert_delivery_routed_delivery_observability.py",
        "recovery-alert-routed-delivery-observability.json",
        "recovery-alert-routed-delivery-observability-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"routed delivery observability workflow missing {fragment}")
    return tuple(errors)


def verify_observation(observation: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    required = (
        "schema_version",
        "generated_at",
        "sample_count",
        "history_count",
        "history_limit",
        "current_route",
        "current_severity",
        "current_delivered",
        "current_attempts",
        "success_count",
        "success_rate",
        "total_attempts",
        "total_retries",
        "retry_rate",
        "average_attempts",
        "max_attempts",
        "average_latency_seconds",
        "max_latency_seconds",
        "route_counts",
        "failure_counts",
        "transport_failure_count",
        "terminal_http_failure_count",
        "retryable_http_failure_count",
    )
    for field in required:
        if field not in observation:
            errors.append(f"routed delivery observability missing field {field}")

    for field in ("success_rate", "retry_rate"):
        value = observation.get(field)
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            errors.append(f"routed delivery observability {field} must be 0..1")

    for field in (
        "sample_count",
        "history_count",
        "total_attempts",
        "total_retries",
        "max_attempts",
    ):
        value = observation.get(field)
        if not isinstance(value, int) or value < 0:
            errors.append(f"routed delivery observability {field} must be non-negative")

    for field in ("route_counts", "failure_counts"):
        if not isinstance(observation.get(field), dict):
            errors.append(f"routed delivery observability {field} must be an object")

    forbidden = ("endpoint_url", "hmac_secret", "signature", "authorization", "webhook_url")
    serialized = json.dumps(observation, sort_keys=True).lower()
    for fragment in forbidden:
        if fragment in serialized:
            errors.append(
                f"routed delivery observability contains forbidden field/material {fragment}"
            )
    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--observation", type=Path)
    args = parser.parse_args()
    errors = list(verify_configuration())

    if args.observation is not None:
        try:
            data = json.loads(args.observation.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"unable to load observability artifact: {exc}")
        else:
            if not isinstance(data, dict):
                errors.append("routed delivery observability must be a JSON object")
            else:
                errors.extend(verify_observation(data))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert routed delivery observability policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
