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
    policy = alerting.get("routed_slo_alert_delivery_slo_alerting")
    if not isinstance(policy, dict):
        raise ValueError("routed SLO alert delivery SLO alerting policy is missing")
    return policy


def _severity(status: str) -> str:
    return {
        "PASS": "NONE",
        "WARN": "ADVISORY",
        "FAIL": "CRITICAL",
        "INSUFFICIENT_SAMPLES": "NONE",
    }.get(status, "NONE")


def build_alert(
    slo: dict[str, Any],
    trend: dict[str, Any] | None,
    history: dict[str, Any] | None,
    policy: dict[str, Any],
) -> dict[str, Any]:
    status = str(slo.get("status", "INSUFFICIENT_SAMPLES"))
    severity = _severity(status)
    trend_name = trend.get("trend") if isinstance(trend, dict) else None
    trend_authoritative = bool(trend.get("authoritative")) if isinstance(trend, dict) else False
    if (
        severity == "NONE"
        and trend_authoritative
        and trend_name == "WORSENING"
        and bool(policy.get("alert_on_worsening_trend", True))
    ):
        severity = "ADVISORY"
    consecutive = 0
    if isinstance(history, dict) and isinstance(history.get("records"), list):
        for record in reversed(history["records"]):
            if not isinstance(record, dict):
                continue
            if str(record.get("status")) == "PASS":
                break
            if bool(record.get("authoritative")):
                consecutive += 1
    if severity in {"ADVISORY", "CRITICAL"} and consecutive >= int(
        policy.get("escalate_after_consecutive_non_passing", 3)
    ):
        severity = "ESCALATED"
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "delivery_id": slo.get("delivery_id"),
        "route": slo.get("route"),
        "source_status": status,
        "severity": severity,
        "trend": trend_name,
        "trend_authoritative": trend_authoritative,
        "consecutive_non_passing": consecutive,
        "external_delivery_enabled": bool(policy.get("external_delivery_enabled", False)),
    }


def render_summary(alert: dict[str, Any]) -> str:
    return (
        "## Routed SLO Alert Delivery SLO Alert\n\n"
        f"- Severity: {alert['severity']}\n"
        f"- Source status: {alert['source_status']}\n"
        f"- Trend: {alert['trend']}\n"
        f"- Trend authoritative: {str(alert['trend_authoritative']).lower()}\n"
        f"- Consecutive non-passing: {alert['consecutive_non_passing']}\n"
        f"- External delivery enabled: {str(alert['external_delivery_enabled']).lower()}\n"
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--slo", type=Path, required=True)
    p.add_argument("--trend", type=Path)
    p.add_argument("--history", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    a = p.parse_args()
    trend = _load_json(a.trend) if a.trend and a.trend.exists() else None
    history = _load_json(a.history) if a.history and a.history.exists() else None
    alert = build_alert(_load_json(a.slo), trend, history, _load_policy(a.policy))
    a.output.write_text(json.dumps(alert, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    a.summary.write_text(render_summary(alert), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
