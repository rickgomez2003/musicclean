"""Verify routed-delivery SLO escalation and routing policy."""

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
        "severity_routes": {
            "NONE": "none",
            "ADVISORY": "operations",
            "CRITICAL": "incident-response",
            "ESCALATED": "incident-response",
        },
        "escalated_route": "incident-response",
        "external_delivery_enabled": False,
    }

    if alerting.get("routed_delivery_slo_routing") != expected:
        errors.append("routed recovery alert delivery SLO routing policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    for fragment in (
        "Build routed recovery alert delivery SLO route",
        "Verify routed recovery alert delivery SLO route",
        "Publish routed recovery alert delivery SLO route summary",
        "build_recovery_alert_routed_delivery_slo_route.py",
        "verify_recovery_alert_delivery_routed_delivery_slo_routing.py",
        "recovery-alert-routed-delivery-slo-route.json",
        "recovery-alert-routed-delivery-slo-route-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"routed delivery SLO routing workflow missing {fragment}")

    return tuple(errors)


def verify_route(route: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []

    required = (
        "schema_version",
        "generated_at",
        "route_required",
        "route",
        "severity",
        "escalated",
        "source_route",
        "source_severity",
        "alert_required",
        "reasons",
        "external_delivery_enabled",
    )

    for field in required:
        if field not in route:
            errors.append(f"routed delivery SLO route missing field {field}")

    if route.get("schema_version") != 1:
        errors.append("routed delivery SLO route schema_version must be 1")

    if route.get("route") not in {
        "none",
        "operations",
        "incident-response",
    }:
        errors.append("routed delivery SLO route is invalid")

    if route.get("severity") not in {
        "NONE",
        "ADVISORY",
        "CRITICAL",
        "ESCALATED",
    }:
        errors.append("routed delivery SLO route severity is invalid")

    if route.get("external_delivery_enabled") is not False:
        errors.append("routed delivery SLO route external delivery must remain disabled")

    if not isinstance(route.get("reasons"), list):
        errors.append("routed delivery SLO route reasons must be a list")

    serialized = json.dumps(route, sort_keys=True).lower()
    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
    ):
        if fragment in serialized:
            errors.append(f"routed delivery SLO route contains forbidden field/material {fragment}")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    if args.route is not None:
        try:
            data = json.loads(args.route.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"unable to load routed delivery SLO route: {exc}")
        else:
            if not isinstance(data, dict):
                errors.append("routed delivery SLO route must be a JSON object")
            else:
                errors.extend(verify_route(data))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert routed delivery SLO escalation and routing policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
