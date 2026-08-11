"""Build provider-neutral logical routes from routed-delivery SLO alerts."""

from __future__ import annotations

import argparse
import json
import tomllib
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

    policy = alerting.get("routed_slo_alert_delivery_routed_delivery_slo_routing")
    if not isinstance(policy, dict):
        raise ValueError("routed SLO alert delivery routed-delivery SLO routing policy is missing")
    return policy


def build_route(alert: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    authoritative = alert.get("authoritative") is True
    alerting = alert.get("alert") is True
    severity = alert.get("severity")
    escalated = alert.get("escalated") is True

    if not authoritative or not alerting or severity == "NONE":
        route = str(policy["none_route"])
        reason = "suppressed_or_no_alert"
    elif escalated:
        route = str(policy["escalated_route"])
        reason = "escalated_alert"
    elif severity == "CRITICAL":
        route = str(policy["critical_route"])
        reason = "critical_alert"
    elif severity == "ADVISORY":
        route = str(policy["advisory_route"])
        reason = "advisory_alert"
    else:
        route = str(policy["none_route"])
        reason = "unsupported_alert_state"

    return {
        "schema_version": 1,
        "delivery_id": alert.get("delivery_id"),
        "logical_route": route,
        "route_reason": reason,
        "source_alert_severity": severity,
        "source_alert_escalated": escalated,
        "source_alert_authoritative": authoritative,
        "provider_neutral": bool(policy.get("provider_neutral", True)),
        "external_delivery_enabled": bool(policy.get("external_delivery_enabled", False)),
    }


def verify_secret_safe(route: dict[str, Any]) -> tuple[str, ...]:
    serialized = json.dumps(route, sort_keys=True).lower()
    errors: list[str] = []
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


def render_summary(route: dict[str, Any]) -> str:
    return "\n".join(
        [
            "## Routed Recovery SLO Alert Delivery — Routed Delivery SLO Escalation & Routing",
            "",
            f"- Logical route: `{route['logical_route']}`",
            f"- Route reason: `{route['route_reason']}`",
            f"- Source severity: `{route['source_alert_severity']}`",
            f"- Source escalated: `{route['source_alert_escalated']}`",
            f"- Source authoritative: `{route['source_alert_authoritative']}`",
            f"- Provider neutral: `{route['provider_neutral']}`",
            f"- External delivery enabled: `{route['external_delivery_enabled']}`",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--alert", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    route = build_route(_load_json(args.alert), _load_policy(args.policy))
    errors = verify_secret_safe(route)
    if errors:
        raise ValueError("; ".join(errors))

    args.output.write_text(
        json.dumps(route, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.summary.write_text(render_summary(route), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
