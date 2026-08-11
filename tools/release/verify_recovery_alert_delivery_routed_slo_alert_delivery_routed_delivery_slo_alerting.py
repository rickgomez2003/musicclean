"""Verify routed-delivery SLO alerting policy and evidence."""

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
        "alert_on_warn": True,
        "alert_on_fail": True,
        "alert_on_worsening_trend": True,
        "escalate_after_consecutive_non_passing": 3,
        "external_delivery_enabled": False,
        "provider_neutral": True,
    }

    if alerting.get("routed_slo_alert_delivery_routed_delivery_slo_alerting") != expected:
        errors.append("routed SLO alert delivery routed-delivery SLO alerting policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "Build routed recovery SLO alert delivery routed delivery SLO alert",
        "Verify routed recovery SLO alert delivery routed delivery SLO alerting",
        "build_recovery_alert_routed_slo_delivery_routed_delivery_slo_alert.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_slo_alerting.py",
        "recovery-alert-routed-slo-delivery-routed-delivery-slo-alert.json",
        "recovery-alert-routed-slo-delivery-routed-delivery-slo-alert-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"routed-delivery SLO alerting workflow missing {fragment}")

    return tuple(errors)


def verify_alert(alert: Any) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(alert, dict):
        return ("SLO alert must be a JSON object",)

    if alert.get("schema_version") != 1:
        errors.append("SLO alert schema_version must be 1")

    if alert.get("severity") not in {"NONE", "ADVISORY", "CRITICAL"}:
        errors.append("SLO alert severity is invalid")

    if not isinstance(alert.get("alert"), bool):
        errors.append("SLO alert flag must be boolean")

    if not isinstance(alert.get("authoritative"), bool):
        errors.append("SLO alert authoritative must be boolean")

    if alert.get("provider_neutral") is not True:
        errors.append("SLO alerting must remain provider neutral")

    if alert.get("external_delivery_enabled") is not False:
        errors.append("SLO alerting external delivery must remain disabled")

    if alert.get("authoritative") is False and alert.get("alert") is True:
        errors.append("non-authoritative SLO evidence must not alert")

    serialized = json.dumps(alert, sort_keys=True).lower()
    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
        "request_headers",
    ):
        if fragment in serialized:
            errors.append(f"SLO alert contains forbidden material {fragment}")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alert", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    if args.alert is not None:
        errors.extend(verify_alert(json.loads(args.alert.read_text(encoding="utf-8"))))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert routed SLO alert delivery routed delivery SLO alerting policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
