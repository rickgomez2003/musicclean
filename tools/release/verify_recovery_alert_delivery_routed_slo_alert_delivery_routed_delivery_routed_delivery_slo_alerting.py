from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_FRAGMENTS = (
    "endpoint_url",
    "hmac_secret",
    "signature",
    "authorization",
    "webhook_url",
    "request_headers",
    "https://",
    "http://",
)


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    with (root / "release/recovery-alerting.toml").open("rb") as stream:
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        return ("recovery alerting policy is missing",)

    expected = {
        "schema_version": 1,
        "escalation_threshold": 3,
        "worsening_trend_escalates_advisory": True,
        "insufficient_evidence_alerts": False,
        "external_delivery_enabled": False,
        "provider_neutral": True,
        "secret_safe": True,
    }

    key = "routed_slo_alert_delivery_routed_delivery_routed_delivery_slo_alerting"
    if alerting.get(key) != expected:
        errors.append("routed-delivery SLO alerting policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    fragments = (
        ("Build routed recovery SLO alert delivery routed delivery routed delivery SLO alert"),
        ("Verify routed recovery SLO alert delivery routed delivery routed delivery SLO alerting"),
        ("build_recovery_alert_routed_slo_delivery_routed_delivery_routed_delivery_slo_alert.py"),
        (
            "verify_recovery_alert_delivery_routed_slo_alert_delivery_"
            "routed_delivery_routed_delivery_slo_alerting.py"
        ),
        "recovery-alert-routed-slo-delivery-routed-delivery-slo-alert.json",
    )

    for fragment in fragments:
        if fragment not in workflow:
            errors.append(f"workflow missing {fragment}")

    return tuple(errors)


def verify_report(report: Any) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(report, dict):
        return ("SLO alert evidence must be a JSON object",)

    if report.get("schema_version") != 1:
        errors.append("alert schema_version must be 1")

    if report.get("alert_state") not in {
        "NONE",
        "ADVISORY",
        "CRITICAL",
        "ESCALATED",
        "NON_AUTHORITATIVE",
    }:
        errors.append("alert_state is invalid")

    if report.get("severity") not in {
        "none",
        "warning",
        "critical",
    }:
        errors.append("severity is invalid")

    if not isinstance(report.get("should_alert"), bool):
        errors.append("should_alert must be a boolean")

    if report.get("external_delivery_enabled") is not False:
        errors.append("external delivery must remain disabled")

    if report.get("provider_neutral") is not True:
        errors.append("alert evidence must remain provider-neutral")

    if report.get("slo_authoritative") is not True and report.get("should_alert") is not False:
        errors.append("non-authoritative SLO evidence must not trigger alerts")

    serialized = json.dumps(report, sort_keys=True).lower()
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment in serialized:
            errors.append(f"alert evidence contains forbidden material {fragment}")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    if args.report is not None:
        errors.extend(verify_report(json.loads(args.report.read_text(encoding="utf-8"))))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        "recovery alert routed SLO alert delivery routed delivery "
        "routed delivery SLO alerting policy verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
