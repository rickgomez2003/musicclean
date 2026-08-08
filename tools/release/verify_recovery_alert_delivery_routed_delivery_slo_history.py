"""Verify routed-delivery SLO history and trend policy."""

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
        "short_window": 4,
        "long_window": 12,
        "minimum_trend_samples": 4,
        "trend_tolerance": 0.000001,
        "retain_days": 90,
        "deduplicate": True,
    }

    if alerting.get("routed_delivery_slo_history") != expected:
        errors.append("routed recovery alert delivery SLO history policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    for fragment in (
        "Build routed recovery alert delivery SLO history",
        "Analyze routed recovery alert delivery SLO trends",
        "Verify routed recovery alert delivery SLO history",
        "Publish routed recovery alert delivery SLO trend summary",
        "build_recovery_alert_routed_delivery_slo_history.py",
        "analyze_recovery_alert_routed_delivery_slo_trends.py",
        "verify_recovery_alert_delivery_routed_delivery_slo_history.py",
        "recovery-alert-routed-delivery-slo-history.json",
        "recovery-alert-routed-delivery-slo-trend.json",
        "recovery-alert-routed-delivery-slo-trend-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"routed delivery SLO history workflow missing {fragment}")

    return tuple(errors)


def verify_history(history: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []

    if history.get("schema_version") != 1:
        errors.append("routed delivery SLO history schema_version must be 1")

    records = history.get("records")
    if not isinstance(records, list):
        return ("routed delivery SLO history records must be a list",)

    if history.get("record_count") != len(records):
        errors.append("routed delivery SLO history record_count must match records")

    history_limit = history.get("history_limit")
    if not isinstance(history_limit, int) or history_limit < 1:
        errors.append("routed delivery SLO history history_limit must be positive")
    elif len(records) > history_limit:
        errors.append("routed delivery SLO history exceeds configured history_limit")

    return tuple(errors)


def verify_trend(trend: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []

    if trend.get("schema_version") != 1:
        errors.append("routed delivery SLO trend schema_version must be 1")

    if trend.get("sample_gate") not in {
        "READY",
        "INSUFFICIENT_SAMPLES",
    }:
        errors.append("routed delivery SLO trend sample_gate is invalid")

    if trend.get("overall_trend") not in {
        "IMPROVING",
        "STABLE",
        "WORSENING",
        "INSUFFICIENT_SAMPLES",
    }:
        errors.append("routed delivery SLO overall_trend is invalid")

    metric_trends = trend.get("metric_trends")
    if not isinstance(metric_trends, list):
        errors.append("routed delivery SLO metric_trends must be a list")

    serialized = json.dumps(trend, sort_keys=True).lower()
    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
    ):
        if fragment in serialized:
            errors.append(f"routed delivery SLO trend contains forbidden field/material {fragment}")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path)
    parser.add_argument("--trend", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    if args.history is not None:
        try:
            history = json.loads(args.history.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"unable to load SLO history: {exc}")
        else:
            if not isinstance(history, dict):
                errors.append("routed delivery SLO history must be a JSON object")
            else:
                errors.extend(verify_history(history))

    if args.trend is not None:
        try:
            trend = json.loads(args.trend.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"unable to load SLO trend: {exc}")
        else:
            if not isinstance(trend, dict):
                errors.append("routed delivery SLO trend must be a JSON object")
            else:
                errors.extend(verify_trend(trend))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert routed delivery SLO history and trend policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
