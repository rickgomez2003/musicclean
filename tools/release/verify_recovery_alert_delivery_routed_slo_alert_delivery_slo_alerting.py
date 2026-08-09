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
        doc = tomllib.load(stream)
    alerting = doc.get("alerting")
    expected = {
        "schema_version": 1,
        "warn_severity": "ADVISORY",
        "fail_severity": "CRITICAL",
        "worsening_trend_severity": "ADVISORY",
        "alert_on_worsening_trend": True,
        "escalate_after_consecutive_non_passing": 3,
        "external_delivery_enabled": False,
        "provider_neutral": True,
    }
    if (
        not isinstance(alerting, dict)
        or alerting.get("routed_slo_alert_delivery_slo_alerting") != expected
    ):
        errors.append("routed SLO alert delivery SLO alerting policy is invalid")
    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "Build routed recovery SLO alert delivery SLO alert",
        "Verify routed recovery SLO alert delivery SLO alerting",
        "Publish routed recovery SLO alert delivery SLO alert summary",
        "build_recovery_alert_routed_slo_delivery_slo_alert.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_slo_alerting.py",
        "recovery-alert-routed-slo-delivery-slo-alert.json",
    ):
        if fragment not in workflow:
            errors.append(f"routed SLO alert delivery SLO alerting workflow missing {fragment}")
    return tuple(errors)


def verify_alert(alert: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    if alert.get("schema_version") != 1:
        errors.append("routed SLO alert delivery SLO alert schema_version must be 1")
    if alert.get("severity") not in {"NONE", "ADVISORY", "CRITICAL", "ESCALATED"}:
        errors.append("routed SLO alert delivery SLO alert severity is invalid")
    if alert.get("external_delivery_enabled") is not False:
        errors.append("routed SLO alert delivery SLO external delivery must remain disabled")
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
            errors.append(
                f"routed SLO alert delivery SLO alert contains forbidden material {fragment}"
            )
    return tuple(errors)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--alert", type=Path)
    a = p.parse_args()
    errors = list(verify_configuration())
    if a.alert:
        data = json.loads(a.alert.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            errors.append("routed SLO alert delivery SLO alert must be a JSON object")
        else:
            errors.extend(verify_alert(data))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("recovery alert routed SLO alert delivery SLO alerting policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
