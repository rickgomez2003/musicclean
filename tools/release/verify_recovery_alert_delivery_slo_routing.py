"""Verify recovery alert delivery SLO escalation and routing."""

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
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        return ("recovery alerting policy is missing",)

    expected = {
        "schema_version": 1,
        "default_route": "operations",
        "escalation_route": "incident-response",
        "consecutive_nonpass_escalation": 3,
        "escalate_worsening_critical": True,
        "external_delivery_enabled": False,
        "routes": {
            "advisory": "operations",
            "critical": "operations",
            "escalated": "incident-response",
        },
    }
    if alerting.get("slo_routing") != expected:
        errors.append("recovery alert delivery SLO routing policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    for fragment in (
        "Build recovery alert delivery SLO route",
        "Verify recovery alert delivery SLO route",
        "Publish recovery delivery SLO routing summary",
        "recovery-alert-delivery-slo-route.json",
        "recovery-alert-delivery-slo-route-summary.md",
    ):
        if fragment not in workflow:
            errors.append(f"delivery SLO routing workflow missing {fragment}")

    return tuple(errors)


def verify_route(path: Path) -> tuple[str, ...]:
    try:
        route = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load delivery SLO route: {exc}",)

    if not isinstance(route, dict):
        return ("delivery SLO route must be a JSON object",)

    errors: list[str] = []
    for field in (
        "schema_version",
        "generated_at",
        "provider",
        "external_delivery_enabled",
        "route_required",
        "route",
        "severity",
        "escalation_required",
        "consecutive_warn_fail",
        "trend_status",
        "reasons",
    ):
        if field not in route:
            errors.append(f"delivery SLO route missing field {field}")

    if route.get("provider") != "provider-neutral":
        errors.append("delivery SLO route provider must be provider-neutral")
    if route.get("external_delivery_enabled") is not False:
        errors.append("delivery SLO route external delivery must remain disabled")
    if route.get("route_required") and route.get("route") == "none":
        errors.append("required route cannot be none")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())
    if args.route is not None:
        errors.extend(verify_route(args.route))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("recovery alert delivery SLO escalation and routing policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
