"""Build provider-neutral alert evidence for routed-delivery SLOs."""

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
    policy = alerting.get("routed_delivery_slo_alerting")
    if not isinstance(policy, dict):
        raise ValueError("alerting.routed_delivery_slo_alerting policy is missing")
    return policy


def _recent_nonpass_count(history: dict[str, Any]) -> int:
    raw = history.get("records")
    records = [x for x in raw if isinstance(x, dict)] if isinstance(raw, list) else []
    count = 0
    for record in reversed(records):
        if str(record.get("status")) in {"WARN", "FAIL"}:
            count += 1
        else:
            break
    return count


def build_alert(
    slo_report: dict[str, Any],
    trend_report: dict[str, Any],
    history: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    status = str(slo_report.get("status", "PASS"))
    authoritative = bool(slo_report.get("authoritative"))
    trend = str(trend_report.get("overall_trend", "INSUFFICIENT_SAMPLES"))
    trend_authoritative = bool(trend_report.get("authoritative"))
    reasons: list[str] = []
    severity = "NONE"
    alert_required = False

    if authoritative and status == "FAIL":
        alert_required = True
        severity = str(policy.get("fail_severity", "CRITICAL"))
        reasons.append("current routed-delivery SLO status is FAIL")
    elif authoritative and status == "WARN":
        alert_required = True
        severity = str(policy.get("warn_severity", "ADVISORY"))
        reasons.append("current routed-delivery SLO status is WARN")

    if (
        bool(policy.get("alert_on_worsening_trend", True))
        and trend_authoritative
        and trend == "WORSENING"
    ):
        alert_required = True
        if severity == "NONE":
            severity = str(policy.get("worsening_severity", "ADVISORY"))
        reasons.append("authoritative routed-delivery SLO trend is worsening")

    consecutive = _recent_nonpass_count(history)
    threshold = max(int(policy.get("consecutive_nonpass_escalation", 2)), 1)
    escalated = alert_required and consecutive >= threshold
    if escalated:
        severity = str(policy.get("escalated_severity", "ESCALATED"))
        reasons.append("consecutive routed-delivery SLO non-pass threshold reached")

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "alert_required": alert_required,
        "severity": severity,
        "escalated": escalated,
        "reasons": reasons,
        "current_status": status,
        "current_authoritative": authoritative,
        "trend": trend,
        "trend_authoritative": trend_authoritative,
        "consecutive_nonpass_count": consecutive,
        "consecutive_nonpass_escalation": threshold,
        "current_route": slo_report.get("current_route"),
        "current_severity": slo_report.get("current_severity"),
        "external_delivery_enabled": bool(policy.get("external_delivery_enabled", False)),
    }


def render_summary(alert: dict[str, Any]) -> str:
    lines = [
        "## Routed Recovery Alert Delivery SLO Alert",
        "",
        f"- Alert required: {str(alert['alert_required']).lower()}",
        f"- Severity: **{alert['severity']}**",
        f"- Escalated: {str(alert['escalated']).lower()}",
        f"- Current SLO status: {alert['current_status']}",
        f"- Trend: {alert['trend']}",
        f"- Consecutive non-pass count: {alert['consecutive_nonpass_count']}",
        "",
        "### Reasons",
        "",
    ]
    lines.extend(f"- {r}" for r in alert["reasons"]) if alert["reasons"] else lines.append(
        "- No alert conditions are active"
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--slo-report", type=Path, required=True)
    parser.add_argument("--trend-report", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    alert = build_alert(
        _load_json(args.slo_report),
        _load_json(args.trend_report),
        _load_json(args.history),
        _load_policy(args.policy),
    )
    args.output.write_text(json.dumps(alert, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.summary.write_text(render_summary(alert), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
