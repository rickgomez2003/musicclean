"""Build provider-neutral escalation and routing for routed-delivery SLO alerts."""

from __future__ import annotations

import argparse
import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_policy(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("alerting policy is missing")

    policy = alerting.get("routed_delivery_slo_routing")
    if not isinstance(policy, dict):
        raise ValueError("alerting.routed_delivery_slo_routing policy is missing")

    return policy


def build_route(
    alert: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    alert_required = bool(alert.get("alert_required"))
    severity = str(alert.get("severity", "NONE"))
    source_route = alert.get("current_route")

    route_map = policy.get("severity_routes")
    if not isinstance(route_map, dict):
        raise ValueError("severity_routes policy is missing")

    route = str(route_map.get(severity, "none"))
    reasons: list[str] = []

    if not alert_required:
        route = "none"
        reasons.append("no routed-delivery SLO alert is required")
    else:
        reasons.append(f"routed-delivery SLO alert severity {severity} maps to {route}")

    if bool(alert.get("escalated")):
        escalated_route = str(policy.get("escalated_route", "incident-response"))
        if escalated_route != route:
            route = escalated_route
            reasons.append("escalated routed-delivery SLO alert overrides route")

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "route_required": route != "none",
        "route": route,
        "severity": severity,
        "escalated": bool(alert.get("escalated")),
        "source_route": source_route,
        "source_severity": alert.get("current_severity"),
        "alert_required": alert_required,
        "reasons": reasons,
        "external_delivery_enabled": bool(policy.get("external_delivery_enabled", False)),
    }


def render_summary(route: dict[str, Any]) -> str:
    lines = [
        "## Routed Recovery Alert Delivery SLO Escalation & Routing",
        "",
        f"- Route required: {str(route['route_required']).lower()}",
        f"- Route: **{route['route']}**",
        f"- Severity: {route['severity']}",
        f"- Escalated: {str(route['escalated']).lower()}",
        f"- Source route: {route['source_route']}",
        "",
        "### Reasons",
        "",
    ]

    if route["reasons"]:
        lines.extend(f"- {reason}" for reason in route["reasons"])
    else:
        lines.append("- No routing reasons were recorded")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--alert", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    route = build_route(
        _load_json(args.alert),
        _load_policy(args.policy),
    )

    args.output.write_text(
        json.dumps(route, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.summary.write_text(
        render_summary(route),
        encoding="utf-8",
    )

    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
