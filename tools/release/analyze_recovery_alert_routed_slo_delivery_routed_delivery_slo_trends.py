"""Analyze trends across routed-delivery SLO history."""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path
from typing import Any

METRICS = (
    "success_rate",
    "retry_rate",
    "average_attempts",
    "transport_failure_rate",
)


def _load_json(path: Path) -> list[dict[str, Any]]:
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

    policy = alerting.get("routed_slo_alert_delivery_routed_delivery_slo_history")
    if not isinstance(policy, dict):
        raise ValueError("routed SLO alert delivery routed-delivery SLO history policy is missing")
    return policy


def _metric_value(entry: dict[str, Any], metric: str) -> float | None:
    metrics = entry.get("metrics")
    if not isinstance(metrics, dict):
        return None
    payload = metrics.get(metric)
    if not isinstance(payload, dict):
        return None
    value = payload.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _trend(metric: str, first: float, last: float, tolerance: float) -> str:
    delta = last - first
    if abs(delta) <= tolerance:
        return "STABLE"

    lower_is_better = metric in {
        "retry_rate",
        "average_attempts",
        "transport_failure_rate",
    }
    if lower_is_better:
        return "WORSENING" if delta > 0 else "IMPROVING"
    return "IMPROVING" if delta > 0 else "WORSENING"


def analyze(
    history: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    minimum = max(2, int(policy.get("trend_minimum_samples", 3)))
    tolerance = max(0.0, float(policy.get("trend_tolerance", 0.0)))

    authoritative_entries = [entry for entry in history if entry.get("authoritative") is True]
    authoritative = len(authoritative_entries) >= minimum

    metrics: dict[str, dict[str, Any]] = {}
    for metric in METRICS:
        values = [
            value
            for entry in authoritative_entries
            if (value := _metric_value(entry, metric)) is not None
        ]

        if not authoritative or len(values) < minimum:
            metrics[metric] = {
                "trend": "INSUFFICIENT_SAMPLES",
                "first": values[0] if values else None,
                "last": values[-1] if values else None,
                "delta": (values[-1] - values[0] if len(values) >= 2 else None),
            }
            continue

        first = values[0]
        last = values[-1]
        metrics[metric] = {
            "trend": _trend(metric, first, last, tolerance),
            "first": first,
            "last": last,
            "delta": last - first,
        }

    trend_values = {item["trend"] for item in metrics.values()}
    if not authoritative:
        overall = "INSUFFICIENT_SAMPLES"
    elif "WORSENING" in trend_values:
        overall = "WORSENING"
    elif "IMPROVING" in trend_values:
        overall = "IMPROVING"
    else:
        overall = "STABLE"

    return {
        "schema_version": 1,
        "history_count": len(history),
        "authoritative_sample_count": len(authoritative_entries),
        "minimum_samples": minimum,
        "authoritative": authoritative,
        "overall_trend": overall,
        "metrics": metrics,
    }


def verify_secret_safe(report: dict[str, Any]) -> tuple[str, ...]:
    serialized = json.dumps(report, sort_keys=True).lower()
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
            errors.append(f"SLO trend contains forbidden material {fragment}")
    return tuple(errors)


def render_summary(report: dict[str, Any]) -> str:
    lines = [
        "## Routed Recovery SLO Alert Delivery — Routed Delivery SLO History & Trends",
        "",
        f"- Overall trend: `{report['overall_trend']}`",
        f"- Authoritative: `{report['authoritative']}`",
        f"- History records: `{report['history_count']}`",
        (f"- Authoritative samples: `{report['authoritative_sample_count']}`"),
        f"- Minimum samples: `{report['minimum_samples']}`",
        "",
        "### Metric trends",
        "",
    ]

    for name, metric in report["metrics"].items():
        lines.append(
            f"- {name}: `{metric['trend']}` "
            f"(first=`{metric['first']}`, last=`{metric['last']}`, "
            f"delta=`{metric['delta']}`)"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    report = analyze(_load_json(args.history), _load_policy(args.policy))
    errors = verify_secret_safe(report)
    if errors:
        raise ValueError("; ".join(errors))

    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.summary.write_text(render_summary(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
