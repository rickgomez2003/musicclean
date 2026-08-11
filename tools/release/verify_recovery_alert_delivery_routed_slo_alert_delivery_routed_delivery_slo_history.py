"""Verify routed-delivery SLO history and trend policy/evidence."""

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
        "max_records": 30,
        "trend_minimum_samples": 3,
        "trend_tolerance": 0.0,
        "external_export_enabled": False,
    }

    if alerting.get("routed_slo_alert_delivery_routed_delivery_slo_history") != expected:
        errors.append("routed SLO alert delivery routed-delivery SLO history policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    for fragment in (
        "Build routed recovery SLO alert delivery routed delivery SLO history",
        "Analyze routed recovery SLO alert delivery routed delivery SLO trends",
        "Verify routed recovery SLO alert delivery routed delivery SLO history",
        "build_recovery_alert_routed_slo_delivery_routed_delivery_slo_history.py",
        "analyze_recovery_alert_routed_slo_delivery_routed_delivery_slo_trends.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_slo_history.py",
        "recovery-alert-routed-slo-delivery-routed-delivery-slo-history.json",
        "recovery-alert-routed-slo-delivery-routed-delivery-slo-trends.json",
    ):
        if fragment not in workflow:
            errors.append(f"routed-delivery SLO history workflow missing {fragment}")

    return tuple(errors)


def verify_history(history: Any) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(history, list):
        return ("SLO history must be a JSON array",)

    if len(history) > 30:
        errors.append("SLO history exceeds configured bound")

    delivery_ids: list[str] = []
    for item in history:
        if not isinstance(item, dict):
            errors.append("SLO history records must be objects")
            continue

        delivery_id = item.get("delivery_id")
        if not isinstance(delivery_id, str) or not delivery_id:
            errors.append("SLO history delivery_id is required")
        else:
            delivery_ids.append(delivery_id)

        if item.get("overall_classification") not in {
            "PASS",
            "WARN",
            "FAIL",
            "INSUFFICIENT_SAMPLES",
        }:
            errors.append("SLO history classification is invalid")

    if len(delivery_ids) != len(set(delivery_ids)):
        errors.append("SLO history delivery_id values must be unique")

    serialized = json.dumps(history, sort_keys=True).lower()
    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
        "request_headers",
    ):
        if fragment in serialized:
            errors.append(f"SLO history contains forbidden material {fragment}")

    return tuple(errors)


def verify_trend(report: Any) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(report, dict):
        return ("SLO trend report must be a JSON object",)

    if report.get("schema_version") != 1:
        errors.append("SLO trend schema_version must be 1")

    if report.get("overall_trend") not in {
        "IMPROVING",
        "WORSENING",
        "STABLE",
        "INSUFFICIENT_SAMPLES",
    }:
        errors.append("SLO overall trend is invalid")

    if not isinstance(report.get("authoritative"), bool):
        errors.append("SLO trend authoritative must be boolean")

    metrics = report.get("metrics")
    if not isinstance(metrics, dict):
        errors.append("SLO trend metrics must be an object")
    else:
        expected = {
            "success_rate",
            "retry_rate",
            "average_attempts",
            "transport_failure_rate",
        }
        if set(metrics) != expected:
            errors.append("SLO trend metrics set is invalid")

    serialized = json.dumps(report, sort_keys=True).lower()
    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
        "request_headers",
    ):
        if fragment in serialized:
            errors.append(f"SLO trend contains forbidden material {fragment}")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path)
    parser.add_argument("--trend", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    if args.history is not None:
        errors.extend(verify_history(json.loads(args.history.read_text(encoding="utf-8"))))

    if args.trend is not None:
        errors.extend(verify_trend(json.loads(args.trend.read_text(encoding="utf-8"))))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        "recovery alert routed SLO alert delivery routed delivery "
        "SLO history and trend policy verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
