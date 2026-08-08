"""Analyze routed-delivery SLO history and produce trend evidence."""

from __future__ import annotations

import argparse
import json
import statistics
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STATUS_RANK = {
    "PASS": 0,
    "WARN": 1,
    "FAIL": 2,
}


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

    policy = alerting.get("routed_delivery_slo_history")
    if not isinstance(policy, dict):
        raise ValueError("alerting.routed_delivery_slo_history policy is missing")

    return policy


def _metric_values(
    records: list[dict[str, Any]],
    metric: str,
) -> list[float]:
    values: list[float] = []

    for record in records:
        evaluations = record.get("evaluations")
        if not isinstance(evaluations, list):
            continue

        for item in evaluations:
            if not isinstance(item, dict):
                continue
            if item.get("metric") != metric:
                continue

            value = item.get("value")
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                values.append(float(value))
            break

    return values


def _direction(
    short_mean: float,
    long_mean: float,
    metric_direction: str,
    tolerance: float,
) -> str:
    delta = short_mean - long_mean

    if abs(delta) <= tolerance:
        return "STABLE"

    if metric_direction == "higher-is-better":
        return "IMPROVING" if delta > 0 else "WORSENING"

    return "IMPROVING" if delta < 0 else "WORSENING"


def analyze(
    history: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    raw_records = history.get("records")
    records = (
        [item for item in raw_records if isinstance(item, dict)]
        if isinstance(raw_records, list)
        else []
    )

    short_window = max(int(policy.get("short_window", 4)), 1)
    long_window = max(int(policy.get("long_window", 12)), short_window)
    minimum_samples = max(int(policy.get("minimum_trend_samples", 4)), 1)
    tolerance = float(policy.get("trend_tolerance", 0.000001))

    authoritative = len(records) >= minimum_samples

    metric_directions: dict[str, str] = {}
    for record in records:
        evaluations = record.get("evaluations")
        if not isinstance(evaluations, list):
            continue
        for item in evaluations:
            if isinstance(item, dict) and item.get("metric"):
                metric_directions.setdefault(
                    str(item["metric"]),
                    str(item.get("direction", "lower-is-better")),
                )

    metric_trends: list[dict[str, Any]] = []

    for metric in sorted(metric_directions):
        values = _metric_values(records, metric)
        if not values:
            continue

        short_values = values[-short_window:]

        baseline_end = max(len(values) - len(short_values), 0)
        baseline_start = max(baseline_end - long_window, 0)
        long_values = values[baseline_start:baseline_end]

        if not long_values:
            split = max(len(values) // 2, 1)
            long_values = values[:split]
            short_values = values[split:]

        short_mean = statistics.fmean(short_values)
        long_mean = statistics.fmean(long_values)

        trend = (
            _direction(
                short_mean,
                long_mean,
                metric_directions[metric],
                tolerance,
            )
            if authoritative
            else "INSUFFICIENT_SAMPLES"
        )

        metric_trends.append(
            {
                "metric": metric,
                "direction": metric_directions[metric],
                "sample_count": len(values),
                "short_window": len(short_values),
                "long_window": len(long_values),
                "short_mean": short_mean,
                "long_mean": long_mean,
                "delta": short_mean - long_mean,
                "trend": trend,
            }
        )

    status_ranks = [STATUS_RANK.get(str(item.get("status")), 0) for item in records[-short_window:]]

    worsening = any(item["trend"] == "WORSENING" for item in metric_trends)
    improving = (
        bool(metric_trends)
        and not worsening
        and any(item["trend"] == "IMPROVING" for item in metric_trends)
    )

    if not authoritative:
        overall_trend = "INSUFFICIENT_SAMPLES"
    elif worsening:
        overall_trend = "WORSENING"
    elif improving:
        overall_trend = "IMPROVING"
    else:
        overall_trend = "STABLE"

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "record_count": len(records),
        "minimum_trend_samples": minimum_samples,
        "authoritative": authoritative,
        "sample_gate": "READY" if authoritative else "INSUFFICIENT_SAMPLES",
        "short_window": short_window,
        "long_window": long_window,
        "overall_trend": overall_trend,
        "recent_status_max": max(status_ranks, default=0),
        "metric_trends": metric_trends,
    }


def render_summary(report: dict[str, Any]) -> str:
    lines = [
        "## Routed Recovery Alert Delivery SLO History & Trends",
        "",
        f"- Sample gate: {report['sample_gate']}",
        f"- Records: {report['record_count']}",
        (f"- Minimum trend samples: {report['minimum_trend_samples']}"),
        f"- Overall trend: **{report['overall_trend']}**",
        "",
        "| Metric | Short Mean | Long Mean | Trend |",
        "|---|---:|---:|---|",
    ]

    for item in report["metric_trends"]:
        lines.append(
            f"| {item['metric']} | "
            f"{item['short_mean']:.6f} | "
            f"{item['long_mean']:.6f} | "
            f"{item['trend']} |"
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    report = analyze(
        _load_json(args.history),
        _load_policy(args.policy),
    )

    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.summary.write_text(
        render_summary(report),
        encoding="utf-8",
    )

    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
