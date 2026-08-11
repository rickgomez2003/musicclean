"""Verify routed-delivery SLO escalation and routing policy/evidence."""

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
        "none_route": "none",
        "advisory_route": "operations",
        "critical_route": "incident-response",
        "escalated_route": "incident-response",
        "external_delivery_enabled": False,
        "provider_neutral": True,
    }

    if alerting.get("routed_slo_alert_delivery_routed_delivery_slo_routing") != expected:
        errors.append("routed SLO alert delivery routed-delivery SLO routing policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "Build routed recovery SLO alert delivery routed delivery SLO route",
        "Verify routed recovery SLO alert delivery routed delivery SLO routing",
        "build_recovery_alert_routed_slo_delivery_routed_delivery_slo_route.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_slo_routing.py",
        "recovery-alert-routed-slo-delivery-routed-delivery-slo-route.json",
        "recovery-alert-routed-slo-delivery-routed-delivery-slo-route-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"routed-delivery SLO routing workflow missing {fragment}")

    return tuple(errors)


def verify_route(route: Any) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(route, dict):
        return ("SLO route must be a JSON object",)

    if route.get("schema_version") != 1:
        errors.append("SLO route schema_version must be 1")

    if route.get("logical_route") not in {
        "none",
        "operations",
        "incident-response",
    }:
        errors.append("SLO logical route is invalid")

    if route.get("provider_neutral") is not True:
        errors.append("SLO routing must remain provider neutral")

    if route.get("external_delivery_enabled") is not False:
        errors.append("SLO routing external delivery must remain disabled")

    if route.get("source_alert_authoritative") is False and route.get("logical_route") != "none":
        errors.append("non-authoritative alert evidence must route to none")

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
            errors.append(f"SLO route contains forbidden material {fragment}")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    if args.route is not None:
        errors.extend(verify_route(json.loads(args.route.read_text(encoding="utf-8"))))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        "recovery alert routed SLO alert delivery routed delivery "
        "SLO escalation and routing policy verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
