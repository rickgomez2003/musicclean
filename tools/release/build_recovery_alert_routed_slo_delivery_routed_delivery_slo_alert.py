"""Build provider-neutral alerts from routed-delivery SLO and trend evidence."""

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


def _load_history(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    return [item for item in data if isinstance(item, dict)]


def _load_policy(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("alerting policy is missing")

    policy = alerting.get("routed_slo_alert_delivery_routed_delivery_slo_alerting")
    if not isinstance(policy, dict):
        raise ValueError("routed SLO alert delivery routed-delivery SLO alerting policy is missing")
    return policy


def _consecutive_non_passing(history: list[dict[str, Any]]) -> int:
    count = 0
    for item in reversed(history):
        if item.get("authoritative") is not True:
            break
        if item.get("overall_classification") in {"WARN", "FAIL"}:
            count += 1
            continue
        break
    return count


def build_alert(
    slo: dict[str, Any],
    trend: dict[str, Any],
    history: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    authoritative = slo.get("authoritative") is True
    classification = slo.get("overall_classification")
    overall_trend = trend.get("overall_trend")

    reasons: list[str] = []
    severity = "NONE"

    if authoritative and classification == "FAIL":
        reasons.append("authoritative_slo_fail")
        severity = "CRITICAL"
    elif authoritative and classification == "WARN":
        reasons.append("authoritative_slo_warn")
        severity = "ADVISORY"

    if (
        trend.get("authoritative") is True
        and overall_trend == "WORSENING"
        and bool(policy.get("alert_on_worsening_trend", True))
    ):
        reasons.append("worsening_trend")
        if severity == "NONE":
            severity = "ADVISORY"

    consecutive = _consecutive_non_passing(history)
    threshold = max(
        1,
        int(policy.get("escalate_after_consecutive_non_passing", 3)),
    )
    escalated = authoritative and consecutive >= threshold

    if escalated:
        severity = "CRITICAL"
        reasons.append("consecutive_non_passing_escalation")

    if not authoritative:
        reasons = ["insufficient_samples"]
        severity = "NONE"
        escalated = False

    return {
        "schema_version": 1,
        "delivery_id": slo.get("delivery_id"),
        "logical_route": slo.get("logical_route"),
        "slo_classification": classification,
        "trend_classification": overall_trend,
        "authoritative": authoritative,
        "alert": severity != "NONE",
        "severity": severity,
        "escalated": escalated,
        "consecutive_non_passing": consecutive,
        "reasons": reasons,
        "provider_neutral": bool(policy.get("provider_neutral", True)),
        "external_delivery_enabled": bool(policy.get("external_delivery_enabled", False)),
    }


def verify_secret_safe(alert: dict[str, Any]) -> tuple[str, ...]:
    serialized = json.dumps(alert, sort_keys=True).lower()
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
            errors.append(f"SLO alert contains forbidden material {fragment}")
    return tuple(errors)


def render_summary(alert: dict[str, Any]) -> str:
    lines = [
        "## Routed Recovery SLO Alert Delivery — Routed Delivery SLO Alerting",
        "",
        f"- Alert: `{alert['alert']}`",
        f"- Severity: `{alert['severity']}`",
        f"- Authoritative: `{alert['authoritative']}`",
        f"- SLO classification: `{alert['slo_classification']}`",
        f"- Trend classification: `{alert['trend_classification']}`",
        f"- Escalated: `{alert['escalated']}`",
        f"- Consecutive non-passing: `{alert['consecutive_non_passing']}`",
        f"- Reasons: `{', '.join(alert['reasons'])}`",
        f"- Provider neutral: `{alert['provider_neutral']}`",
        f"- External delivery enabled: `{alert['external_delivery_enabled']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--slo", type=Path, required=True)
    parser.add_argument("--trend", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    alert = build_alert(
        _load_json(args.slo),
        _load_json(args.trend),
        _load_history(args.history),
        _load_policy(args.policy),
    )
    errors = verify_secret_safe(alert)
    if errors:
        raise ValueError("; ".join(errors))

    args.output.write_text(
        json.dumps(alert, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.summary.write_text(render_summary(alert), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
