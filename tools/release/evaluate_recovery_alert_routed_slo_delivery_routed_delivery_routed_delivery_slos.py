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


def _load_policy(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("alerting policy is missing")

    policy = alerting.get("routed_slo_alert_delivery_routed_delivery_routed_delivery_slos")
    if not isinstance(policy, dict):
        raise ValueError("routed-delivery SLO policy is missing")

    return policy


def _metric_status(
    value: float,
    *,
    pass_threshold: float,
    warn_threshold: float,
    higher_is_better: bool,
) -> str:
    if higher_is_better:
        if value >= pass_threshold:
            return "PASS"
        if value >= warn_threshold:
            return "WARN"
        return "FAIL"

    if value <= pass_threshold:
        return "PASS"
    if value <= warn_threshold:
        return "WARN"
    return "FAIL"


def evaluate(
    observability: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    minimum_samples = int(policy.get("minimum_samples", 3))
    sample_count = int(observability.get("sample_count", 1))

    delivery_status = observability.get("delivery_status")
    success_count = int(observability.get("success_count", 0))
    if "success_count" not in observability:
        success_count = 1 if delivery_status == "DELIVERED" else 0

    retry_count_total = int(
        observability.get(
            "retry_count_total",
            observability.get("retry_count", 0),
        )
    )
    attempt_count_total = int(
        observability.get(
            "attempt_count_total",
            observability.get("attempt_count", 0),
        )
    )
    transport_failure_count = int(
        observability.get(
            "transport_failure_count",
            1 if observability.get("transport_failure") else 0,
        )
    )

    denominator = max(1, sample_count)
    delivery_success_rate = success_count / denominator
    retry_rate = min(1.0, retry_count_total / denominator)
    average_attempts = attempt_count_total / denominator
    transport_failure_rate = transport_failure_count / denominator

    if sample_count < minimum_samples:
        overall = "INSUFFICIENT_SAMPLES"
        authoritative = False
        metrics = {
            "delivery_success_rate": "INSUFFICIENT_SAMPLES",
            "retry_rate": "INSUFFICIENT_SAMPLES",
            "average_attempts": "INSUFFICIENT_SAMPLES",
            "transport_failure_rate": "INSUFFICIENT_SAMPLES",
        }
    else:
        metrics = {
            "delivery_success_rate": _metric_status(
                delivery_success_rate,
                pass_threshold=float(policy["delivery_success_rate_pass"]),
                warn_threshold=float(policy["delivery_success_rate_warn"]),
                higher_is_better=True,
            ),
            "retry_rate": _metric_status(
                retry_rate,
                pass_threshold=float(policy["retry_rate_pass"]),
                warn_threshold=float(policy["retry_rate_warn"]),
                higher_is_better=False,
            ),
            "average_attempts": _metric_status(
                average_attempts,
                pass_threshold=float(policy["average_attempts_pass"]),
                warn_threshold=float(policy["average_attempts_warn"]),
                higher_is_better=False,
            ),
            "transport_failure_rate": _metric_status(
                transport_failure_rate,
                pass_threshold=float(policy["transport_failure_rate_pass"]),
                warn_threshold=float(policy["transport_failure_rate_warn"]),
                higher_is_better=False,
            ),
        }

        statuses = set(metrics.values())
        if "FAIL" in statuses:
            overall = "FAIL"
        elif "WARN" in statuses:
            overall = "WARN"
        else:
            overall = "PASS"
        authoritative = True

    return {
        "schema_version": 1,
        "sample_count": sample_count,
        "minimum_samples": minimum_samples,
        "authoritative": authoritative,
        "overall_status": overall,
        "metrics": {
            "delivery_success_rate": {
                "value": round(delivery_success_rate, 6),
                "status": metrics["delivery_success_rate"],
            },
            "retry_rate": {
                "value": round(retry_rate, 6),
                "status": metrics["retry_rate"],
            },
            "average_attempts": {
                "value": round(average_attempts, 6),
                "status": metrics["average_attempts"],
            },
            "transport_failure_rate": {
                "value": round(transport_failure_rate, 6),
                "status": metrics["transport_failure_rate"],
            },
        },
        "provider_neutral": True,
        "external_export_enabled": False,
    }


def render_summary(report: dict[str, Any]) -> str:
    lines = [
        "## Routed Delivery SLOs",
        "",
        f"- Overall status: `{report.get('overall_status')}`",
        f"- Authoritative: `{report.get('authoritative')}`",
        f"- Sample count: `{report.get('sample_count')}`",
        f"- Minimum samples: `{report.get('minimum_samples')}`",
        "",
        "| Metric | Value | Status |",
        "|---|---:|---|",
    ]

    metrics = report.get("metrics", {})
    if isinstance(metrics, dict):
        for name in (
            "delivery_success_rate",
            "retry_rate",
            "average_attempts",
            "transport_failure_rate",
        ):
            item = metrics.get(name, {})
            if isinstance(item, dict):
                lines.append(f"| {name} | {item.get('value')} | {item.get('status')} |")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--observability", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    report = evaluate(
        _load_json(args.observability),
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

    print("recovery alert routed SLO alert delivery routed delivery routed delivery SLOs evaluated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
