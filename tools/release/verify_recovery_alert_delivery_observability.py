"""Verify recovery alert delivery observability policy and workflow."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    with (root / "release" / "recovery-alerting.toml").open("rb") as stream:
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        return ("recovery alerting policy is missing",)

    observability = alerting.get("observability")
    expected = {
        "schema_version": 1,
        "history_limit": 52,
        "short_window": 4,
        "long_window": 12,
        "minimum_trend_samples": 4,
        "publish_step_summary": True,
        "retain_days": 90,
        "record_attempt_count": True,
        "record_retry_count": True,
        "record_failure_class": True,
        "record_status_code": True,
        "record_delivery_latency": True,
        "record_delivery_id": True,
        "record_destination": False,
        "record_secret_material": False,
    }
    if observability != expected:
        errors.append("recovery alert delivery observability policy is invalid")

    workflow = (
        root / ".github" / "workflows" / "orion-recovery-drill.yml"
    ).read_text(encoding="utf-8")

    required = (
        "Collect prior delivery evidence",
        "Build recovery delivery observability",
        "build_recovery_delivery_observability.py",
        "Verify recovery delivery observability",
        "verify_recovery_alert_delivery_observability.py",
        "recovery-alert-delivery-observability.json",
        "recovery-alert-delivery-summary.md",
        "GITHUB_STEP_SUMMARY",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"recovery delivery observability missing {fragment}")

    forbidden = (
        "RECOVERY_ALERT_WEBHOOK_URL >",
        "RECOVERY_ALERT_WEBHOOK_HMAC_SECRET >",
        "print(webhook_url",
        "print(hmac_secret",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"observability workflow contains secret leak pattern {fragment}")

    return tuple(errors)


def verify_observation(path: Path) -> tuple[str, ...]:
    try:
        observation = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load delivery observability evidence: {exc}",)

    if not isinstance(observation, dict):
        return ("delivery observability evidence must be an object",)

    required = (
        "schema_version",
        "generated_at",
        "delivery_id",
        "delivery_required",
        "delivered",
        "attempt_count",
        "retry_count",
        "status_code",
        "failure_class",
        "provider",
        "sample_count",
        "required_sample_count",
        "delivered_sample_count",
        "success_rate",
        "average_latency_seconds",
        "maximum_latency_seconds",
        "history_limit",
    )
    errors: list[str] = []
    for field in required:
        if field not in observation:
            errors.append(f"delivery observability evidence missing field {field}")

    if observation.get("schema_version") != 1:
        errors.append("delivery observability schema version must be 1")

    success_rate = observation.get("success_rate")
    if not isinstance(success_rate, (int, float)) or not 0 <= success_rate <= 1:
        errors.append("delivery observability success rate must be between 0 and 1")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--observation", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())
    if args.observation is not None:
        errors.extend(verify_observation(args.observation))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.observation is None:
        print("recovery alert delivery observability policy verified")
    else:
        print(f"recovery alert delivery observability verified: {args.observation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
