"""Evaluate policy-driven SLOs for routed SLO alert-delivery routed delivery."""

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
    policy = alerting.get("routed_slo_alert_delivery_routed_delivery_slos")
    if not isinstance(policy, dict):
        raise ValueError("routed SLO alert delivery routed-delivery SLO policy is missing")
    return policy


def _classify(value: float, *, warn: float, fail: float, lower_is_better: bool) -> str:
    if lower_is_better:
        if value >= fail:
            return "FAIL"
        if value >= warn:
            return "WARN"
        return "PASS"
    if value <= fail:
        return "FAIL"
    if value <= warn:
        return "WARN"
    return "PASS"


def evaluate(observation: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    sample_count = int(policy.get("sample_count", 1))
    minimum_samples = int(policy.get("minimum_samples", 1))
    authoritative = sample_count >= minimum_samples

    success_rate = 1.0 if bool(observation.get("delivered", False)) else 0.0
    retry_rate = 1.0 if int(observation.get("retry_count", 0)) > 0 else 0.0
    average_attempts = float(observation.get("attempt_count", 0))
    transport_failure_rate = (
        1.0 if observation.get("failure_classification") == "transport_error" else 0.0
    )

    metrics = {
        "success_rate": {
            "value": success_rate,
            "classification": _classify(
                success_rate,
                warn=float(policy["success_rate_warn"]),
                fail=float(policy["success_rate_fail"]),
                lower_is_better=False,
            ),
        },
        "retry_rate": {
            "value": retry_rate,
            "classification": _classify(
                retry_rate,
                warn=float(policy["retry_rate_warn"]),
                fail=float(policy["retry_rate_fail"]),
                lower_is_better=True,
            ),
        },
        "average_attempts": {
            "value": average_attempts,
            "classification": _classify(
                average_attempts,
                warn=float(policy["average_attempts_warn"]),
                fail=float(policy["average_attempts_fail"]),
                lower_is_better=True,
            ),
        },
        "transport_failure_rate": {
            "value": transport_failure_rate,
            "classification": _classify(
                transport_failure_rate,
                warn=float(policy["transport_failure_rate_warn"]),
                fail=float(policy["transport_failure_rate_fail"]),
                lower_is_better=True,
            ),
        },
    }

    if not authoritative:
        overall = "INSUFFICIENT_SAMPLES"
        for metric in metrics.values():
            metric["classification"] = "INSUFFICIENT_SAMPLES"
    else:
        classes = {metric["classification"] for metric in metrics.values()}
        if "FAIL" in classes:
            overall = "FAIL"
        elif "WARN" in classes:
            overall = "WARN"
        else:
            overall = "PASS"

    return {
        "schema_version": 1,
        "delivery_id": observation.get("delivery_id"),
        "logical_route": observation.get("logical_route"),
        "sample_count": sample_count,
        "minimum_samples": minimum_samples,
        "authoritative": authoritative,
        "overall_classification": overall,
        "metrics": metrics,
    }


def verify_secret_safe(report: dict[str, Any]) -> tuple[str, ...]:
    serialized = json.dumps(report, sort_keys=True).lower()
    errors = []
    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
        "request_headers",
    ):
        if fragment in serialized:
            errors.append(f"SLO evidence contains forbidden material {fragment}")
    return tuple(errors)


def render_summary(report: dict[str, Any]) -> str:
    lines = [
        "## Routed Recovery SLO Alert Delivery — Routed Delivery SLOs",
        "",
        f"- Overall: `{report['overall_classification']}`",
        f"- Authoritative: `{report['authoritative']}`",
        f"- Samples: `{report['sample_count']}`",
        f"- Minimum samples: `{report['minimum_samples']}`",
        "",
        "### Metrics",
        "",
    ]
    for name, metric in report["metrics"].items():
        lines.append(f"- {name}: `{metric['value']}` — `{metric['classification']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--observation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    report = evaluate(_load_json(args.observation), _load_policy(args.policy))
    errors = verify_secret_safe(report)
    if errors:
        raise ValueError("; ".join(errors))

    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.summary.write_text(render_summary(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
