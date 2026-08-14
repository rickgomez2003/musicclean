from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROUTES = {
    "none",
    "operations",
    "incident_response",
}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def build_route(alert: dict[str, Any]) -> dict[str, Any]:
    alert_state = alert.get("alert_state")
    should_alert = alert.get("should_alert")
    authoritative = alert.get("slo_authoritative")

    if authoritative is not True or should_alert is not True:
        logical_route = "none"
        route_reason = "no_authoritative_alert"
    elif alert_state == "ADVISORY":
        logical_route = "operations"
        route_reason = "advisory_to_operations"
    elif alert_state in {"CRITICAL", "ESCALATED"}:
        logical_route = "incident_response"
        route_reason = "critical_or_escalated_to_incident_response"
    else:
        logical_route = "none"
        route_reason = "unsupported_alert_state"

    report = {
        "schema_version": 1,
        "alert_state": alert_state,
        "severity": alert.get("severity"),
        "should_alert": should_alert is True,
        "slo_authoritative": authoritative is True,
        "logical_route": logical_route,
        "route_reason": route_reason,
        "provider_neutral": True,
        "external_delivery_enabled": False,
    }

    if report["logical_route"] not in ROUTES:
        raise ValueError("invalid logical route")

    return report


def render_summary(report: dict[str, Any]) -> str:
    return (
        "\n".join(
            [
                "## Routed Delivery SLO Escalation & Routing",
                "",
                f"- Alert state: `{report.get('alert_state')}`",
                f"- Severity: `{report.get('severity')}`",
                f"- Should alert: `{report.get('should_alert')}`",
                f"- Logical route: `{report.get('logical_route')}`",
                f"- Route reason: `{report.get('route_reason')}`",
                (f"- SLO authoritative: `{report.get('slo_authoritative')}`"),
            ]
        )
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alert", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    report = build_route(_load_json(args.alert))

    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.summary.write_text(
        render_summary(report),
        encoding="utf-8",
    )

    print(
        "recovery alert routed SLO alert delivery routed delivery "
        "routed delivery SLO escalation and routing built"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
