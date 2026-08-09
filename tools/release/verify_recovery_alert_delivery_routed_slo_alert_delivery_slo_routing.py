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
        "none_route": "none",
        "advisory_route": "operations",
        "critical_route": "incident-response",
        "escalated_route": "incident-response",
        "external_delivery_enabled": False,
        "provider_neutral": True,
    }
    if (
        not isinstance(alerting, dict)
        or alerting.get("routed_slo_alert_delivery_slo_routing") != expected
    ):
        errors.append("routed SLO alert delivery SLO escalation and routing policy is invalid")
    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "Build routed recovery SLO alert delivery SLO route",
        "Verify routed recovery SLO alert delivery SLO routing",
        "Publish routed recovery SLO alert delivery SLO route summary",
        "build_recovery_alert_routed_slo_delivery_slo_route.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_slo_routing.py",
        "recovery-alert-routed-slo-delivery-slo-route.json",
    ):
        if fragment not in workflow:
            errors.append(f"routed SLO alert delivery SLO routing workflow missing {fragment}")
    return tuple(errors)


def verify_route(route: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    if route.get("schema_version") != 1:
        errors.append("routed SLO alert delivery SLO route schema_version must be 1")
    if route.get("route") not in {"none", "operations", "incident-response"}:
        errors.append("routed SLO alert delivery SLO route is invalid")
    if route.get("external_delivery_enabled") is not False:
        errors.append("routed SLO alert delivery SLO external delivery must remain disabled")
    if route.get("provider_neutral") is not True:
        errors.append("routed SLO alert delivery SLO routing must remain provider-neutral")
    serialized = json.dumps(route, sort_keys=True).lower()
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
                f"routed SLO alert delivery SLO route contains forbidden material {fragment}"
            )
    return tuple(errors)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--route", type=Path)
    a = p.parse_args()
    errors = list(verify_configuration())
    if a.route:
        data = json.loads(a.route.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            errors.append("routed SLO alert delivery SLO route must be a JSON object")
        else:
            errors.extend(verify_route(data))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("recovery alert routed SLO alert delivery SLO escalation and routing policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
