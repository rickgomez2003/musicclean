"""Build a provider-neutral recovery SLO alert record."""

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


def _load_history(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("recovery drill history must be a JSON array of objects")
    return data


def _load_policy(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)
    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("recovery alerting policy is missing")
    return alerting


def _consecutive_failures(history: list[dict[str, Any]]) -> int:
    count = 0
    for record in reversed(history):
        if record.get("status") == "FAIL":
            count += 1
        else:
            break
    return count


def build_alert(
    *,
    policy: dict[str, Any],
    slo_report: dict[str, Any],
    trend_report: dict[str, Any],
    history: list[dict[str, Any]],
    now: datetime,
) -> dict[str, Any]:
    severity_policy = policy.get("severity")
    if not isinstance(severity_policy, dict):
        raise ValueError("alert severity policy is missing")

    slo_status = slo_report.get("status")
    if slo_status not in {"PASS", "WARN", "FAIL"}:
        raise ValueError("recovery SLO report status is invalid")

    trend = trend_report.get("duration_trend")
    if trend not in {
        "IMPROVING",
        "STABLE",
        "WORSENING",
        "INSUFFICIENT_DATA",
    }:
        raise ValueError("recovery duration trend is invalid")

    consecutive_failures = _consecutive_failures(history)
    threshold = int(policy["consecutive_failure_escalation"])

    severity: str | None = None
    reasons: list[str] = []

    if slo_status == "FAIL":
        severity = str(severity_policy["fail"])
        reasons.append("recovery SLO status is FAIL")
    elif slo_status == "WARN":
        severity = str(severity_policy["warn"])
        reasons.append("recovery SLO status is WARN")

    if trend == "WORSENING":
        if severity is None:
            severity = str(severity_policy["worsening"])
        reasons.append("recovery duration trend is WORSENING")

    escalated = consecutive_failures >= threshold
    if escalated:
        severity = str(severity_policy["escalated"])
        reasons.append(f"{consecutive_failures} consecutive recovery drill failures")

    latest = history[-1] if history else {}
    alert_required = severity is not None

    return {
        "schema_version": 1,
        "evaluated_at": now.isoformat(),
        "alert_required": alert_required,
        "severity": severity,
        "reasons": reasons,
        "slo_status": slo_status,
        "duration_trend": trend,
        "consecutive_failures": consecutive_failures,
        "escalation_threshold": threshold,
        "escalated": escalated,
        "suppression_window_hours": int(policy["suppression_window_hours"]),
        "provider": str(policy["provider"]),
        "external_delivery_enabled": bool(policy["external_delivery_enabled"]),
        "latest_drill_id": latest.get("drill_id"),
        "latest_drill_status": latest.get("status"),
    }


def render_summary(alert: dict[str, Any]) -> str:
    if alert["alert_required"]:
        heading = f"## Recovery SLO Alert — {alert['severity']}"
    else:
        heading = "## Recovery SLO Status — Healthy"

    lines = [
        heading,
        "",
        f"- SLO status: `{alert['slo_status']}`",
        f"- Duration trend: `{alert['duration_trend']}`",
        f"- Consecutive failures: `{alert['consecutive_failures']}`",
        f"- Escalated: `{str(alert['escalated']).lower()}`",
        f"- Suppression window: `{alert['suppression_window_hours']} hours`",
    ]
    reasons = alert.get("reasons")
    if isinstance(reasons, list) and reasons:
        lines.extend(["", "### Reasons"])
        lines.extend(f"- {reason}" for reason in reasons)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--slo-report", type=Path, required=True)
    parser.add_argument("--trend-report", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()

    alert = build_alert(
        policy=_load_policy(args.policy),
        slo_report=_load_json(args.slo_report),
        trend_report=_load_json(args.trend_report),
        history=_load_history(args.history),
        now=datetime.now(UTC),
    )
    args.output.write_text(
        json.dumps(alert, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.summary is not None:
        args.summary.write_text(render_summary(alert), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
