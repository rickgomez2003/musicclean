"""Verify recovery alert delivery SLO alerting."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []
    with (root / "release/recovery-alerting.toml").open("rb") as stream:
        doc = tomllib.load(stream)
    alerting = doc.get("alerting")
    if not isinstance(alerting, dict):
        return ("recovery alerting policy is missing",)
    expected = {
        "schema_version": 1,
        "minimum_trend_samples": 4,
        "alert_on_worsening_trend": True,
        "consecutive_nonpass_escalation": 2,
        "warn_severity": "ADVISORY",
        "fail_severity": "CRITICAL",
        "worsening_severity": "ADVISORY",
        "escalated_severity": "ESCALATED",
        "external_delivery_enabled": False,
    }
    if alerting.get("slo_alerting") != expected:
        errors.append("recovery alert delivery SLO alerting policy is invalid")
    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "Build recovery alert delivery SLO alert",
        "Verify recovery alert delivery SLO alert",
        "Publish recovery delivery SLO alert summary",
        "recovery-alert-delivery-slo-alert.json",
        "recovery-alert-delivery-slo-alert-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"delivery SLO alerting workflow missing {fragment}")
    return tuple(errors)


def verify_alert(path: Path) -> tuple[str, ...]:
    try:
        alert = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load delivery SLO alert: {exc}",)
    errors: list[str] = []
    if not isinstance(alert, dict):
        return ("delivery SLO alert must be a JSON object",)
    if alert.get("provider") != "provider-neutral":
        errors.append("delivery SLO alert provider must be provider-neutral")
    if alert.get("external_delivery_enabled") is not False:
        errors.append("delivery SLO alert external delivery must remain disabled")
    if alert.get("severity") not in {"NONE", "ADVISORY", "CRITICAL", "ESCALATED"}:
        errors.append("delivery SLO alert severity is invalid")
    if alert.get("alert_required") and not alert.get("reasons"):
        errors.append("required delivery SLO alert must include reasons")
    return tuple(errors)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--alert", type=Path)
    a = p.parse_args()
    errors = list(verify_configuration())
    if a.alert:
        errors.extend(verify_alert(a.alert))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("recovery alert delivery SLO alerting policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
