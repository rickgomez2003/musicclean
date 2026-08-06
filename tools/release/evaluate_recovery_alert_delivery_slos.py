"""Evaluate recovery alert delivery SLOs from observability evidence."""

from __future__ import annotations

import argparse
import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_ORDER = {"INSUFFICIENT_DATA": -1, "PASS": 0, "WARN": 1, "FAIL": 2}


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
        raise ValueError("recovery alerting policy is missing")
    slos = alerting.get("slos")
    if not isinstance(slos, dict):
        raise ValueError("recovery alert delivery SLO policy is missing")
    return slos


def _higher(value: float, warn_below: float, fail_below: float) -> str:
    if value < fail_below:
        return "FAIL"
    if value < warn_below:
        return "WARN"
    return "PASS"


def _lower(value: float, warn_above: float, fail_above: float) -> str:
    if value > fail_above:
        return "FAIL"
    if value > warn_above:
        return "WARN"
    return "PASS"


def evaluate(observation: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    sample_count = int(observation.get("required_sample_count", 0))
    minimum = int(policy["minimum_samples"])
    if sample_count < minimum:
        return {
            "schema_version": int(policy["schema_version"]),
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "INSUFFICIENT_DATA",
            "sample_count": sample_count,
            "minimum_samples": minimum,
            "objectives": {},
            "reasons": [f"need at least {minimum} delivery samples; have {sample_count}"],
        }

    success_rate = float(observation["success_rate"])
    retry_rate = float(observation["retry_rate"])
    terminal_failure_rate = float(observation["terminal_failure_rate"])
    latency_raw = observation.get("average_latency_seconds")
    latency = float(latency_raw) if isinstance(latency_raw, (int, float)) else None

    objectives: dict[str, dict[str, Any]] = {}
    p = policy["success_rate"]
    objectives["success_rate"] = {
        "value": success_rate,
        "status": _higher(success_rate, float(p["warn_below"]), float(p["fail_below"])),
    }
    p = policy["retry_rate"]
    objectives["retry_rate"] = {
        "value": retry_rate,
        "status": _lower(retry_rate, float(p["warn_above"]), float(p["fail_above"])),
    }
    p = policy["terminal_failure_rate"]
    objectives["terminal_failure_rate"] = {
        "value": terminal_failure_rate,
        "status": _lower(terminal_failure_rate, float(p["warn_above"]), float(p["fail_above"])),
    }
    p = policy["average_latency_seconds"]
    objectives["average_latency_seconds"] = {
        "value": latency,
        "status": "INSUFFICIENT_DATA"
        if latency is None
        else _lower(latency, float(p["warn_above"]), float(p["fail_above"])),
    }
    eligible = [
        item["status"] for item in objectives.values() if item["status"] != "INSUFFICIENT_DATA"
    ]
    overall = "INSUFFICIENT_DATA" if not eligible else max(eligible, key=lambda s: _ORDER[s])
    reasons = [
        f"{name}={item['value']} -> {item['status']}"
        for name, item in objectives.items()
        if item["status"] not in {"PASS", "INSUFFICIENT_DATA"}
    ]
    return {
        "schema_version": int(policy["schema_version"]),
        "generated_at": datetime.now(UTC).isoformat(),
        "status": overall,
        "sample_count": sample_count,
        "minimum_samples": minimum,
        "objectives": objectives,
        "reasons": reasons,
    }


def render_summary(report: dict[str, Any]) -> str:
    lines = [
        "## Recovery Alert Delivery SLOs",
        "",
        f"- Overall status: **{report['status']}**",
        f"- Samples: **{report['sample_count']}**",
        f"- Minimum samples: **{report['minimum_samples']}**",
        "",
    ]
    for name, item in report.get("objectives", {}).items():
        lines.append(f"- `{name}`: **{item.get('status')}** (value={item.get('value')})")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--observation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(_load_json(args.observation), _load_policy(args.policy))
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.summary.write_text(render_summary(report), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
