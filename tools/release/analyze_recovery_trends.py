"""Analyze bounded recovery history for rolling SLO trends."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


def _window(records: list[dict[str, Any]], size: int) -> list[dict[str, Any]]:
    if size <= 0:
        raise ValueError("window size must be positive")
    return records[-size:]


def _success_ratio(records: list[dict[str, Any]]) -> float | None:
    if not records:
        return None
    return sum(1 for item in records if item.get("status") == "PASS") / len(records)


def _duration_average(records: list[dict[str, Any]]) -> float | None:
    values = [
        float(item["elapsed_seconds"])
        for item in records
        if isinstance(item.get("elapsed_seconds"), (int, float))
    ]
    return mean(values) if values else None


def _duration_direction(records: list[dict[str, Any]], minimum_samples: int) -> str:
    values = [
        float(item["elapsed_seconds"])
        for item in records
        if isinstance(item.get("elapsed_seconds"), (int, float))
    ]
    if len(values) < minimum_samples:
        return "INSUFFICIENT_DATA"

    midpoint = len(values) // 2
    first = values[:midpoint]
    second = values[midpoint:]
    if not first or not second:
        return "INSUFFICIENT_DATA"

    delta = mean(second) - mean(first)
    tolerance = max(1.0, mean(values) * 0.05)
    if delta > tolerance:
        return "WORSENING"
    if delta < -tolerance:
        return "IMPROVING"
    return "STABLE"


def analyze(
    history: list[dict[str, Any]],
    *,
    short_window: int,
    long_window: int,
    minimum_trend_samples: int,
) -> dict[str, Any]:
    short = _window(history, short_window)
    long = _window(history, long_window)

    return {
        "schema_version": 1,
        "records_available": len(history),
        "latest_drill_id": history[-1].get("drill_id") if history else None,
        "short_window": {
            "requested": short_window,
            "samples": len(short),
            "success_ratio": _success_ratio(short),
            "average_duration_seconds": _duration_average(short),
        },
        "long_window": {
            "requested": long_window,
            "samples": len(long),
            "success_ratio": _success_ratio(long),
            "average_duration_seconds": _duration_average(long),
        },
        "duration_trend": _duration_direction(history, minimum_trend_samples),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--short-window", type=int, required=True)
    parser.add_argument("--long-window", type=int, required=True)
    parser.add_argument("--minimum-trend-samples", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    data = json.loads(args.history.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise ValueError("recovery history must be a JSON array of objects")

    report = analyze(
        data,
        short_window=args.short_window,
        long_window=args.long_window,
        minimum_trend_samples=args.minimum_trend_samples,
    )
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
