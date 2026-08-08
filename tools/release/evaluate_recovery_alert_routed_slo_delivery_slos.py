"""Evaluate SLOs for routed recovery SLO alert delivery observability evidence."""

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
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("alerting policy is missing")

    policy = alerting.get("routed_slo_alert_delivery_slos")
    if not isinstance(policy, dict):
        raise ValueError("routed SLO alert delivery SLO policy is missing")

    return policy


def _status_for_threshold(
    value: float,
    *,
    warn: float,
    fail: float,
    higher_is_better: bool,
) -> str:
    if higher_is_better:
        if value < fail:
            return "FAIL"
        if value < warn:
            return "WARN"
        return "PASS"

    if value > fail:
        return "FAIL"
    if value > warn:
        return "WARN"
    return "PASS"


def evaluate(
    observation: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    metrics = observation.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("observability metrics must be an object")

    minimum_samples = int(policy.get("minimum_samples", 5))
    sample_count = int(policy.get("sample_count", minimum_samples))

    delivered = bool(metrics.get("delivered"))
    retry_count = int(metrics.get("retry_count", 0) or 0)
    attempt_count = int(metrics.get("attempt_count", 0) or 0)
    failure_class = metrics.get("failure_class")

    success_rate = 1.0 if delivered else 0.0
    retry_rate = 1.0 if retry_count > 0 else 0.0
    transport_failure_rate = 1.0 if failure_class == "TRANSPORT" else 0.0

    authoritative = sample_count >= minimum_samples

    results: list[dict[str, Any]] = []

    def add_metric(
        name: str,
        value: float,
        warn: float,
        fail: float,
        higher_is_better: bool,
    ) -> None:
        status = (
            _status_for_threshold(
                value,
                warn=warn,
                fail=fail,
                higher_is_better=higher_is_better,
            )
            if authoritative
            else "INSUFFICIENT_SAMPLES"
        )
        results.append(
            {
                "name": name,
                "value": value,
                "warn": warn,
                "fail": fail,
                "higher_is_better": higher_is_better,
                "status": status,
            }
        )

    add_metric(
        "success_rate",
        success_rate,
        float(policy["success_rate_warn"]),
        float(policy["success_rate_fail"]),
        True,
    )
    add_metric(
        "retry_rate",
        retry_rate,
        float(policy["retry_rate_warn"]),
        float(policy["retry_rate_fail"]),
        False,
    )
    add_metric(
        "average_attempts",
        float(attempt_count),
        float(policy["average_attempts_warn"]),
        float(policy["average_attempts_fail"]),
        False,
    )
    add_metric(
        "transport_failure_rate",
        transport_failure_rate,
        float(policy["transport_failure_rate_warn"]),
        float(policy["transport_failure_rate_fail"]),
        False,
    )

    statuses = {item["status"] for item in results}

    if not authoritative:
        overall = "INSUFFICIENT_SAMPLES"
    elif "FAIL" in statuses:
        overall = "FAIL"
    elif "WARN" in statuses:
        overall = "WARN"
    else:
        overall = "PASS"

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "delivery_id": observation.get("delivery_id"),
        "route": observation.get("route"),
        "authoritative": authoritative,
        "sample_count": sample_count,
        "minimum_samples": minimum_samples,
        "status": overall,
        "metrics": results,
    }


def render_summary(report: dict[str, Any]) -> str:
    lines = [
        "## Routed SLO Alert Delivery SLOs",
        "",
        f"- Status: {report['status']}",
        f"- Authoritative: {str(report['authoritative']).lower()}",
        f"- Sample count: {report['sample_count']}",
        f"- Minimum samples: {report['minimum_samples']}",
        "",
        "| Metric | Value | Status |",
        "| --- | ---: | --- |",
    ]

    for metric in report["metrics"]:
        lines.append(f"| {metric['name']} | {metric['value']:.4f} | {metric['status']} |")

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
