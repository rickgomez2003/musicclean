"""Build a provider-neutral routing decision from recovery alert delivery SLO alerts."""

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
    policy = alerting.get("slo_routing")
    if not isinstance(policy, dict):
        raise ValueError("alerting.slo_routing policy is missing")
    return policy


def build_route(
    alert: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    severity = str(alert.get("severity", "NONE"))
    alert_required = bool(alert.get("alert_required"))
    consecutive = int(alert.get("consecutive_warn_fail", 0))
    trend = str(alert.get("trend_status", "INSUFFICIENT_DATA"))

    route_required = alert_required and severity != "NONE"
    route = "none"
    escalation_required = False
    reasons: list[str] = []

    if route_required:
        route_map = policy["routes"]
        route = str(route_map.get(severity.lower(), policy["default_route"]))
        reasons.append(f"severity {severity} maps to route {route}")

    escalation_threshold = int(policy["consecutive_nonpass_escalation"])
    if route_required and consecutive >= escalation_threshold:
        escalation_required = True
        route = str(policy["escalation_route"])
        reasons.append(
            "consecutive WARN/FAIL escalation threshold reached "
            f"({consecutive} >= {escalation_threshold})"
        )

    if (
        route_required
        and bool(policy["escalate_worsening_critical"])
        and severity in {"CRITICAL", "ESCALATED"}
        and trend == "worsening"
    ):
        escalation_required = True
        route = str(policy["escalation_route"])
        reasons.append("worsening critical delivery SLO alert requires escalation")

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "provider": "provider-neutral",
        "external_delivery_enabled": False,
        "route_required": route_required,
        "route": route,
        "severity": severity,
        "escalation_required": escalation_required,
        "consecutive_warn_fail": consecutive,
        "trend_status": trend,
        "reasons": reasons,
    }


def render_summary(route: dict[str, Any]) -> str:
    lines = [
        "## Recovery Alert Delivery SLO Escalation & Routing",
        "",
        f"- Route required: **{route['route_required']}**",
        f"- Route: **{route['route']}**",
        f"- Severity: **{route['severity']}**",
        f"- Escalation required: **{route['escalation_required']}**",
        f"- Consecutive WARN/FAIL: **{route['consecutive_warn_fail']}**",
        f"- Trend: **{route['trend_status']}**",
        "",
    ]
    if route["reasons"]:
        lines.extend(["### Reasons", ""])
        lines.extend(f"- {reason}" for reason in route["reasons"])
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--alert", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    route = build_route(_load_json(args.alert), _load_policy(args.policy))
    args.output.write_text(
        json.dumps(route, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.summary.write_text(render_summary(route), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
