"""Analyze delivery SLO history trends."""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _values(records: list[dict[str, Any]], name: str) -> list[float]:
    result: list[float] = []
    for record in records:
        objectives = record.get("objectives")
        if not isinstance(objectives, dict):
            continue
        item = objectives.get(name)
        if not isinstance(item, dict):
            continue
        value = item.get("value")
        if isinstance(value, (int, float)):
            result.append(float(value))
    return result


def _classify(short: float, long: float, lower_is_better: bool) -> str:
    if abs(short - long) <= 1e-9:
        return "stable"
    if lower_is_better:
        return "improving" if short < long else "worsening"
    return "improving" if short > long else "worsening"


def analyze(
    history: dict[str, Any],
    short_window: int,
    long_window: int,
    minimum: int,
) -> dict[str, Any]:
    raw = history.get("records")
    records = [r for r in raw if isinstance(r, dict)] if isinstance(raw, list) else []

    counts = {"PASS": 0, "WARN": 0, "FAIL": 0, "INSUFFICIENT_DATA": 0}
    for record in records:
        status = record.get("status")
        if status in counts:
            counts[str(status)] += 1

    consecutive = 0
    for record in reversed(records):
        if record.get("status") in {"WARN", "FAIL"}:
            consecutive += 1
        else:
            break

    result: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "sample_count": len(records),
        "minimum_trend_samples": minimum,
        "status_counts": counts,
        "consecutive_warn_fail": consecutive,
        "trend_status": "INSUFFICIENT_DATA",
        "metrics": {},
    }
    if len(records) < minimum:
        return result

    specs = {
        "success_rate": False,
        "retry_rate": True,
        "terminal_failure_rate": True,
        "average_latency_seconds": True,
    }
    classifications: list[str] = []

    for name, lower_is_better in specs.items():
        short_values = _values(records[-short_window:], name)
        long_values = _values(records[-long_window:], name)
        if not short_values or not long_values:
            continue
        short_avg = statistics.fmean(short_values)
        long_avg = statistics.fmean(long_values)
        classification = _classify(short_avg, long_avg, lower_is_better)
        classifications.append(classification)
        result["metrics"][name] = {
            "short_average": short_avg,
            "long_average": long_avg,
            "classification": classification,
        }

    if "worsening" in classifications:
        result["trend_status"] = "worsening"
    elif "improving" in classifications:
        result["trend_status"] = "improving"
    else:
        result["trend_status"] = "stable"
    return result


def render_summary(report: dict[str, Any]) -> str:
    counts = report["status_counts"]
    lines = [
        "## Recovery Alert Delivery SLO History & Trends",
        "",
        f"- Trend: **{report['trend_status']}**",
        f"- Samples: **{report['sample_count']}**",
        f"- Consecutive WARN/FAIL: **{report['consecutive_warn_fail']}**",
        f"- PASS: **{counts['PASS']}**",
        f"- WARN: **{counts['WARN']}**",
        f"- FAIL: **{counts['FAIL']}**",
        "",
    ]
    for name, item in report.get("metrics", {}).items():
        lines.append(
            f"- `{name}`: **{item['classification']}** "
            f"(short={item['short_average']}, long={item['long_average']})"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--short-window", type=int, required=True)
    parser.add_argument("--long-window", type=int, required=True)
    parser.add_argument("--minimum-trend-samples", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    report = analyze(
        _load(args.history),
        args.short_window,
        args.long_window,
        args.minimum_trend_samples,
    )
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.summary.write_text(render_summary(report), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
