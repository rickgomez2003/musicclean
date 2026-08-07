"""Evaluate routed recovery alert delivery SLOs from observability evidence."""

from __future__ import annotations

import argparse
import json
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

    policy = alerting.get("routed_delivery_slos")
    if not isinstance(policy, dict):
        raise ValueError("alerting.routed_delivery_slos policy is missing")

    return policy


def _higher_is_better(
    metric: str,
    value: float,
    policy: dict[str, Any],
) -> dict[str, Any]:
    warn_below = float(policy["warn_below"])
    fail_below = float(policy["fail_below"])

    if value < fail_below:
        status = "FAIL"
    elif value < warn_below:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "metric": metric,
        "value": value,
        "status": status,
        "warn_threshold": warn_below,
        "fail_threshold": fail_below,
        "direction": "higher-is-better",
    }


def _lower_is_better(
    metric: str,
    value: float,
    policy: dict[str, Any],
) -> dict[str, Any]:
    warn_above = float(policy["warn_above"])
    fail_above = float(policy["fail_above"])

    if value > fail_above:
        status = "FAIL"
    elif value > warn_above:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "metric": metric,
        "value": value,
        "status": status,
        "warn_threshold": warn_above,
        "fail_threshold": fail_above,
        "direction": "lower-is-better",
    }


def evaluate(
    observation: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    sample_count = int(observation.get("sample_count", 0))
    minimum_samples = int(policy["minimum_samples"])
    authoritative = sample_count >= minimum_samples

    terminal_rate = (
        float(observation.get("terminal_http_failure_count", 0)) / sample_count
        if sample_count
        else 0.0
    )
    transport_rate = (
        float(observation.get("transport_failure_count", 0)) / sample_count if sample_count else 0.0
    )

    evaluations = [
        _higher_is_better(
            "success_rate",
            float(observation["success_rate"]),
            policy["success_rate"],
        ),
        _lower_is_better(
            "retry_rate",
            float(observation["retry_rate"]),
            policy["retry_rate"],
        ),
        _lower_is_better(
            "average_attempts",
            float(observation["average_attempts"]),
            policy["average_attempts"],
        ),
        _lower_is_better(
            "average_latency_seconds",
            float(observation["average_latency_seconds"]),
            policy["average_latency_seconds"],
        ),
        _lower_is_better(
            "terminal_http_failure_rate",
            terminal_rate,
            policy["terminal_http_failure_rate"],
        ),
        _lower_is_better(
            "transport_failure_rate",
            transport_rate,
            policy["transport_failure_rate"],
        ),
    ]

    worst = max(
        (item["status"] for item in evaluations),
        key=lambda status: STATUS_RANK[status],
    )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "sample_count": sample_count,
        "minimum_samples": minimum_samples,
        "authoritative": authoritative,
        "sample_gate": "READY" if authoritative else "INSUFFICIENT_SAMPLES",
        "status": worst,
        "evaluations": evaluations,
        "current_route": observation.get("current_route"),
        "current_severity": observation.get("current_severity"),
    }


def render_summary(report: dict[str, Any]) -> str:
    lines = [
        "## Routed Recovery Alert Delivery SLOs",
        "",
        f"- Sample gate: {report['sample_gate']}",
        f"- Samples: {report['sample_count']} / {report['minimum_samples']} minimum",
        f"- Authoritative: {str(report['authoritative']).lower()}",
        f"- Overall status: **{report['status']}**",
        "",
        "### Metrics",
        "",
        "| Metric | Value | Status | Direction |",
        "|---|---:|---|---|",
    ]

    for item in report["evaluations"]:
        lines.append(
            f"| {item['metric']} | {item['value']:.6f} | {item['status']} | {item['direction']} |"
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--observation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    report = evaluate(
        _load_json(args.observation),
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
