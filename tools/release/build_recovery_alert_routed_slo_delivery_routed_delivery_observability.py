"""Build bounded, secret-safe observability for routed SLO alert delivery."""

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

    policy = alerting.get("routed_slo_alert_delivery_routed_delivery_observability")
    if not isinstance(policy, dict):
        raise ValueError(
            "routed SLO alert delivery routed-delivery observability policy is missing"
        )

    return policy


def _bounded_attempts(
    attempts: Any,
    *,
    maximum: int,
) -> list[dict[str, Any]]:
    if not isinstance(attempts, list):
        return []

    bounded: list[dict[str, Any]] = []
    for attempt in attempts[:maximum]:
        if not isinstance(attempt, dict):
            continue
        bounded.append(
            {
                "attempt": attempt.get("attempt"),
                "http_status": attempt.get("http_status"),
                "classification": attempt.get("classification"),
                "retryable": attempt.get("retryable"),
            }
        )
    return bounded


def build_observability(
    receipt: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    maximum = max(0, int(policy.get("max_attempt_records", 10)))
    attempts = _bounded_attempts(receipt.get("attempts"), maximum=maximum)

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "delivery_id": receipt.get("delivery_id"),
        "logical_route": receipt.get("logical_route"),
        "severity": receipt.get("severity"),
        "delivered": bool(receipt.get("delivered", False)),
        "attempt_count": int(receipt.get("attempt_count", 0)),
        "retry_count": int(receipt.get("retry_count", 0)),
        "terminal_http_status": receipt.get("http_status"),
        "failure_classification": receipt.get("failure_classification"),
        "attempts": attempts,
        "attempt_records_truncated": (
            isinstance(receipt.get("attempts"), list) and len(receipt["attempts"]) > maximum
        ),
        "retain_days": int(policy.get("retain_days", 90)),
        "external_export_enabled": bool(policy.get("external_export_enabled", False)),
    }


def verify_secret_safe(report: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    serialized = json.dumps(report, sort_keys=True).lower()

    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
        "request_headers",
    ):
        if fragment in serialized:
            errors.append(f"observability evidence contains forbidden material {fragment}")

    return tuple(errors)


def render_summary(report: dict[str, Any]) -> str:
    lines = [
        "## Routed Recovery SLO Alert Delivery — Routed Delivery Observability",
        "",
        f"- Delivery ID: `{report.get('delivery_id')}`",
        f"- Route: `{report.get('logical_route')}`",
        f"- Severity: `{report.get('severity')}`",
        f"- Delivered: `{report.get('delivered')}`",
        f"- Attempts: `{report.get('attempt_count')}`",
        f"- Retries: `{report.get('retry_count')}`",
        f"- Terminal HTTP status: `{report.get('terminal_http_status')}`",
        f"- Failure classification: `{report.get('failure_classification')}`",
        f"- Attempt records retained: `{len(report.get('attempts', []))}`",
        (f"- Attempt records truncated: `{report.get('attempt_records_truncated')}`"),
        f"- External export enabled: `{report.get('external_export_enabled')}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    report = build_observability(
        _load_json(args.receipt),
        _load_policy(args.policy),
    )

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
