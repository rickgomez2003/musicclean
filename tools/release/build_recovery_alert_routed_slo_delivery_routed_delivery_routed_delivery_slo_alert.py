from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ALERT_STATES = {
    "NONE",
    "ADVISORY",
    "CRITICAL",
    "ESCALATED",
    "NON_AUTHORITATIVE",
}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def build_alert(
    slo: dict[str, Any],
    trend: dict[str, Any],
    *,
    consecutive_non_passing: int = 0,
    escalation_threshold: int = 3,
) -> dict[str, Any]:
    overall_status = slo.get("overall_status")
    authoritative = slo.get("authoritative")
    overall_trend = trend.get("overall_trend")

    if authoritative is not True or overall_status == "INSUFFICIENT_SAMPLES":
        alert_state = "NON_AUTHORITATIVE"
        severity = "none"
        should_alert = False
        reason = "insufficient_authoritative_slo_evidence"
    elif overall_status == "PASS":
        alert_state = "NONE"
        severity = "none"
        should_alert = False
        reason = "slo_pass"
    elif overall_status == "WARN":
        alert_state = "ADVISORY"
        severity = "warning"
        should_alert = True
        reason = "slo_warn"
    elif overall_status == "FAIL":
        alert_state = "CRITICAL"
        severity = "critical"
        should_alert = True
        reason = "slo_fail"
    else:
        alert_state = "NON_AUTHORITATIVE"
        severity = "none"
        should_alert = False
        reason = "unknown_slo_state"

    if should_alert and overall_trend == "WORSENING" and alert_state == "ADVISORY":
        alert_state = "CRITICAL"
        severity = "critical"
        reason = "slo_warn_with_worsening_trend"

    if should_alert and consecutive_non_passing >= escalation_threshold:
        alert_state = "ESCALATED"
        severity = "critical"
        reason = "consecutive_non_passing_threshold_reached"

    report = {
        "schema_version": 1,
        "alert_state": alert_state,
        "severity": severity,
        "should_alert": should_alert,
        "reason": reason,
        "slo_status": overall_status,
        "slo_authoritative": authoritative is True,
        "overall_trend": overall_trend,
        "consecutive_non_passing": consecutive_non_passing,
        "escalation_threshold": escalation_threshold,
        "provider_neutral": True,
        "external_delivery_enabled": False,
    }

    if report["alert_state"] not in ALERT_STATES:
        raise ValueError("invalid alert state")

    return report


def render_summary(report: dict[str, Any]) -> str:
    return (
        "\n".join(
            [
                "## Routed Delivery SLO Alert",
                "",
                f"- Alert state: `{report.get('alert_state')}`",
                f"- Severity: `{report.get('severity')}`",
                f"- Should alert: `{report.get('should_alert')}`",
                f"- Reason: `{report.get('reason')}`",
                f"- SLO status: `{report.get('slo_status')}`",
                f"- Overall trend: `{report.get('overall_trend')}`",
                (f"- Consecutive non-passing: `{report.get('consecutive_non_passing')}`"),
            ]
        )
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slo", type=Path, required=True)
    parser.add_argument("--trend", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--consecutive-non-passing", type=int, default=0)
    parser.add_argument("--escalation-threshold", type=int, default=3)
    args = parser.parse_args()

    report = build_alert(
        _load_json(args.slo),
        _load_json(args.trend),
        consecutive_non_passing=max(0, args.consecutive_non_passing),
        escalation_threshold=max(1, args.escalation_threshold),
    )

    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.summary.write_text(
        render_summary(report),
        encoding="utf-8",
    )

    print(
        "recovery alert routed SLO alert delivery routed delivery routed delivery SLO alert built"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
