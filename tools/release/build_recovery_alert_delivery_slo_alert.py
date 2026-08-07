"""Build provider-neutral recovery alert delivery SLO alert evidence."""

from __future__ import annotations

import argparse
import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

RANK = {"NONE": 0, "ADVISORY": 1, "CRITICAL": 2, "ESCALATED": 3}


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _policy(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)
    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("alerting policy is missing")
    value = alerting.get("slo_alerting")
    if not isinstance(value, dict):
        raise ValueError("alerting.slo_alerting policy is missing")
    return value


def _max_severity(current: str, candidate: str) -> str:
    return candidate if RANK[candidate] > RANK[current] else current


def build_alert(
    slo_report: dict[str, Any],
    trend_report: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    current = str(slo_report.get("status", "INSUFFICIENT_DATA"))
    trend = str(trend_report.get("trend_status", "INSUFFICIENT_DATA"))
    samples = int(trend_report.get("sample_count", 0))
    consecutive = int(trend_report.get("consecutive_warn_fail", 0))
    authoritative = samples >= int(policy["minimum_trend_samples"])
    severity = "NONE"
    reasons: list[str] = []

    if current == "WARN":
        reasons.append("current delivery SLO status is WARN")
        severity = _max_severity(severity, str(policy["warn_severity"]))
    elif current == "FAIL":
        reasons.append("current delivery SLO status is FAIL")
        severity = _max_severity(severity, str(policy["fail_severity"]))

    if bool(policy["alert_on_worsening_trend"]) and authoritative and trend == "worsening":
        reasons.append("delivery SLO trend is worsening")
        severity = _max_severity(severity, str(policy["worsening_severity"]))

    threshold = int(policy["consecutive_nonpass_escalation"])
    if consecutive >= threshold:
        reasons.append(f"consecutive WARN/FAIL threshold reached ({consecutive} >= {threshold})")
        severity = _max_severity(severity, str(policy["escalated_severity"]))

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "provider": "provider-neutral",
        "external_delivery_enabled": False,
        "alert_required": bool(reasons),
        "severity": severity,
        "current_slo_status": current,
        "trend_status": trend,
        "trend_authoritative": authoritative,
        "sample_count": samples,
        "consecutive_warn_fail": consecutive,
        "reasons": reasons,
    }


def summary(alert: dict[str, Any]) -> str:
    lines = [
        "## Recovery Alert Delivery SLO Alert",
        "",
        f"- Alert required: **{alert['alert_required']}**",
        f"- Severity: **{alert['severity']}**",
        f"- Current SLO status: **{alert['current_slo_status']}**",
        f"- Trend: **{alert['trend_status']}**",
        f"- Trend authoritative: **{alert['trend_authoritative']}**",
        f"- Consecutive WARN/FAIL: **{alert['consecutive_warn_fail']}**",
        "",
    ]
    if alert["reasons"]:
        lines += ["### Reasons", ""] + [f"- {x}" for x in alert["reasons"]] + [""]
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--slo-report", type=Path, required=True)
    p.add_argument("--trend-report", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    a = p.parse_args()
    alert = build_alert(_json(a.slo_report), _json(a.trend_report), _policy(a.policy))
    a.output.write_text(json.dumps(alert, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    a.summary.write_text(summary(alert), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
