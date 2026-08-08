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
        "max_attempt_records": 10,
        "retain_days": 90,
        "external_export_enabled": False,
    }
    if (
        not isinstance(alerting, dict)
        or alerting.get("routed_slo_alert_delivery_observability") != expected
    ):
        errors.append("routed SLO alert delivery observability policy is invalid")
    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "Build routed recovery SLO alert delivery observability",
        "Verify routed recovery SLO alert delivery observability",
        "build_recovery_alert_routed_slo_delivery_observability.py",
        "recovery-alert-routed-slo-delivery-observability.json",
    ):
        if fragment not in workflow:
            errors.append(f"observability workflow missing {fragment}")
    return tuple(errors)


def verify_report(report: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    if report.get("schema_version") != 1:
        errors.append("observability schema_version must be 1")
    if report.get("external_export_enabled") is not False:
        errors.append("observability external export must remain disabled")
    if not isinstance(report.get("metrics"), dict):
        errors.append("observability metrics must be an object")
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
            errors.append(f"observability contains forbidden material {fragment}")
    return tuple(errors)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=Path)
    a = p.parse_args()
    errors = list(verify_configuration())
    if a.report:
        data = json.loads(a.report.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            errors.append("observability report must be a JSON object")
        else:
            errors.extend(verify_report(data))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("recovery alert routed SLO alert delivery observability policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
