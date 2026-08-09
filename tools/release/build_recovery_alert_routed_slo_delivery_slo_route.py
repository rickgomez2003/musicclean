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
        doc = tomllib.load(stream)
    alerting = doc.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("alerting policy is missing")
    policy = alerting.get("routed_slo_alert_delivery_slo_routing")
    if not isinstance(policy, dict):
        raise ValueError("routed SLO alert delivery SLO routing policy is missing")
    return policy


def build_route(alert: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    severity = str(alert.get("severity", "NONE"))
    routes = {
        "NONE": str(policy.get("none_route", "none")),
        "ADVISORY": str(policy.get("advisory_route", "operations")),
        "CRITICAL": str(policy.get("critical_route", "incident-response")),
        "ESCALATED": str(policy.get("escalated_route", "incident-response")),
    }
    route = routes.get(severity, routes["NONE"])
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "delivery_id": alert.get("delivery_id"),
        "source_route": alert.get("route"),
        "severity": severity,
        "route": route,
        "external_delivery_enabled": bool(policy.get("external_delivery_enabled", False)),
        "provider_neutral": bool(policy.get("provider_neutral", True)),
    }


def render_summary(route: dict[str, Any]) -> str:
    return (
        "## Routed SLO Alert Delivery SLO Escalation & Routing\n\n"
        f"- Severity: {route['severity']}\n"
        f"- Logical route: {route['route']}\n"
        f"- Provider neutral: {str(route['provider_neutral']).lower()}\n"
        f"- External delivery enabled: {str(route['external_delivery_enabled']).lower()}\n"
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--alert", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    a = p.parse_args()
    route = build_route(_load_json(a.alert), _load_policy(a.policy))
    a.output.write_text(json.dumps(route, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    a.summary.write_text(render_summary(route), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
