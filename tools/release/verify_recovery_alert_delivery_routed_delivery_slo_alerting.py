"""Verify routed-delivery SLO alerting policy and alert artifacts."""

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
        "alert_on_worsening_trend": True,
        "consecutive_nonpass_escalation": 2,
        "warn_severity": "ADVISORY",
        "fail_severity": "CRITICAL",
        "worsening_severity": "ADVISORY",
        "escalated_severity": "ESCALATED",
        "external_delivery_enabled": False,
    }
    if alerting.get("routed_delivery_slo_alerting") != expected:
        errors.append("routed recovery alert delivery SLO alerting policy is invalid")
    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "Build routed recovery alert delivery SLO alert",
        "Verify routed recovery alert delivery SLO alert",
        "Publish routed recovery alert delivery SLO alert summary",
        "build_recovery_alert_routed_delivery_slo_alert.py",
        "verify_recovery_alert_delivery_routed_delivery_slo_alerting.py",
        "recovery-alert-routed-delivery-slo-alert.json",
        "recovery-alert-routed-delivery-slo-alert-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"routed delivery SLO alerting workflow missing {fragment}")
    return tuple(errors)


def verify_alert(alert: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    for field in (
        "schema_version",
        "generated_at",
        "alert_required",
        "severity",
        "escalated",
        "reasons",
        "current_status",
        "current_authoritative",
        "trend",
        "trend_authoritative",
        "consecutive_nonpass_count",
        "consecutive_nonpass_escalation",
        "current_route",
        "current_severity",
        "external_delivery_enabled",
    ):
        if field not in alert:
            errors.append(f"routed delivery SLO alert missing field {field}")
    if alert.get("schema_version") != 1:
        errors.append("routed delivery SLO alert schema_version must be 1")
    if alert.get("severity") not in {"NONE", "ADVISORY", "CRITICAL", "ESCALATED"}:
        errors.append("routed delivery SLO alert severity is invalid")
    if alert.get("external_delivery_enabled") is not False:
        errors.append("routed delivery SLO alert external delivery must remain disabled")
    if not isinstance(alert.get("reasons"), list):
        errors.append("routed delivery SLO alert reasons must be a list")
    serialized = json.dumps(alert, sort_keys=True).lower()
    for fragment in ("endpoint_url", "hmac_secret", "signature", "authorization", "webhook_url"):
        if fragment in serialized:
            errors.append(f"routed delivery SLO alert contains forbidden field/material {fragment}")
    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alert", type=Path)
    args = parser.parse_args()
    errors = list(verify_configuration())
    if args.alert is not None:
        try:
            data = json.loads(args.alert.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"unable to load routed delivery SLO alert: {exc}")
        else:
            if not isinstance(data, dict):
                errors.append("routed delivery SLO alert must be a JSON object")
            else:
                errors.extend(verify_alert(data))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("recovery alert routed delivery SLO alerting policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
