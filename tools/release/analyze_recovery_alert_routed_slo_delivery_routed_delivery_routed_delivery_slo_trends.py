from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

METRIC_DIRECTIONS = {
    "delivery_success_rate": True,
    "retry_rate": False,
    "average_attempts": False,
    "transport_failure_rate": False,
}


def _metric_value(
    entry: dict[str, Any],
    name: str,
) -> float | None:
    metrics = entry.get("metrics")
    if not isinstance(metrics, dict):
        return None

    metric = metrics.get(name)
    if not isinstance(metric, dict):
        return None

    value = metric.get("value")
    if isinstance(value, (int, float)):
        return float(value)

    return None


def analyze_trends(
    history: list[dict[str, Any]],
    *,
    minimum_samples: int = 4,
    window_size: int = 3,
    epsilon: float = 1e-6,
) -> dict[str, Any]:
    authoritative = [
        entry for entry in history if isinstance(entry, dict) and entry.get("authoritative") is True
    ]

    report: dict[str, Any] = {
        "schema_version": 1,
        "history_count": len(history),
        "authoritative_history_count": len(authoritative),
        "minimum_samples": minimum_samples,
        "window_size": window_size,
        "overall_trend": "INSUFFICIENT_HISTORY",
        "metrics": {},
        "provider_neutral": True,
        "external_export_enabled": False,
    }

    if len(authoritative) < minimum_samples:
        return report

    metrics: dict[str, Any] = {}

    for name, higher_is_better in METRIC_DIRECTIONS.items():
        values = [
            value for entry in authoritative if (value := _metric_value(entry, name)) is not None
        ]

        if len(values) < minimum_samples:
            metrics[name] = {
                "trend": "INSUFFICIENT_HISTORY",
                "delta": None,
            }
            continue

        window = min(window_size, max(1, len(values) // 2))
        previous = mean(values[-2 * window : -window])
        current = mean(values[-window:])
        delta = current - previous

        if abs(delta) <= epsilon:
            trend = "STABLE"
        elif (delta > 0 and higher_is_better) or (delta < 0 and not higher_is_better):
            trend = "IMPROVING"
        else:
            trend = "WORSENING"

        metrics[name] = {
            "previous_average": round(previous, 6),
            "current_average": round(current, 6),
            "delta": round(delta, 6),
            "trend": trend,
        }

    report["metrics"] = metrics

    trends = {item.get("trend") for item in metrics.values() if isinstance(item, dict)}

    if "WORSENING" in trends:
        report["overall_trend"] = "WORSENING"
    elif "IMPROVING" in trends:
        report["overall_trend"] = "IMPROVING"
    elif trends and trends <= {"STABLE"}:
        report["overall_trend"] = "STABLE"

    return report


def render_summary(report: dict[str, Any]) -> str:
    lines = [
        "## Routed Delivery SLO History & Trends",
        "",
        f"- Overall trend: `{report.get('overall_trend')}`",
        f"- History count: `{report.get('history_count')}`",
        (f"- Authoritative history count: `{report.get('authoritative_history_count')}`"),
        "",
        "| Metric | Previous | Current | Delta | Trend |",
        "|---|---:|---:|---:|---|",
    ]

    metrics = report.get("metrics")
    if isinstance(metrics, dict):
        for name in METRIC_DIRECTIONS:
            item = metrics.get(name, {})
            if not isinstance(item, dict):
                continue

            lines.append(
                "| "
                + " | ".join(
                    [
                        name,
                        str(item.get("previous_average")),
                        str(item.get("current_average")),
                        str(item.get("delta")),
                        str(item.get("trend")),
                    ]
                )
                + " |"
            )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--minimum-samples", type=int, default=4)
    parser.add_argument("--window-size", type=int, default=3)
    args = parser.parse_args()

    raw_history = json.loads(args.history.read_text(encoding="utf-8"))
    if not isinstance(raw_history, list):
        raise ValueError("history must be a JSON array")

    report = analyze_trends(
        [item for item in raw_history if isinstance(item, dict)],
        minimum_samples=max(2, args.minimum_samples),
        window_size=max(1, args.window_size),
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
        "recovery alert routed SLO alert delivery routed delivery "
        "routed delivery SLO trends analyzed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
