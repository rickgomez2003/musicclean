"""Verify routed SLO alert delivery SLO history and trend policy."""

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
        "max_records": 52,
        "minimum_trend_samples": 4,
        "short_window": 2,
        "long_window": 4,
        "read_only": True,
    }

    if alerting.get("routed_slo_alert_delivery_slo_history") != expected:
        errors.append("routed SLO alert delivery SLO history policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    for fragment in (
        "Build routed recovery SLO alert delivery SLO history",
        "Analyze routed recovery SLO alert delivery SLO trends",
        "Verify routed recovery SLO alert delivery SLO history",
        "build_recovery_alert_routed_slo_delivery_slo_history.py",
        "analyze_recovery_alert_routed_slo_delivery_slo_trends.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_slo_history.py",
        "recovery-alert-routed-slo-delivery-slo-history.json",
        "recovery-alert-routed-slo-delivery-slo-trends.json",
    ):
        if fragment not in workflow:
            errors.append(f"routed SLO alert delivery SLO history workflow missing {fragment}")

    return tuple(errors)


def verify_evidence(data: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []

    serialized = json.dumps(data, sort_keys=True).lower()

    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
        "request_headers",
    ):
        if fragment in serialized:
            errors.append(
                f"routed SLO alert delivery SLO history contains forbidden material {fragment}"
            )

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path)
    parser.add_argument("--trend", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    for path in (args.history, args.trend):
        if path is None:
            continue

        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            errors.append(f"{path} must contain a JSON object")
            continue

        errors.extend(verify_evidence(data))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert routed SLO alert delivery SLO history and trend policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
