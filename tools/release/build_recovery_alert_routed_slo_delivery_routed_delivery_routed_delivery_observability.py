from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

FORBIDDEN_FRAGMENTS = (
    "endpoint_url",
    "hmac_secret",
    "signature",
    "authorization",
    "webhook_url",
    "request_headers",
    "https://",
    "http://",
)


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def build_observability(
    receipt: dict[str, Any],
    *,
    max_attempt_records: int = 3,
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    raw_attempts = receipt.get("attempts")
    if isinstance(raw_attempts, list):
        for attempt in raw_attempts[:max_attempt_records]:
            if isinstance(attempt, dict):
                attempts.append(
                    {
                        "attempt": attempt.get("attempt"),
                        "delivery_id": attempt.get("delivery_id"),
                        "status": attempt.get("status"),
                        "http_status": attempt.get("http_status"),
                        "failure_classification": attempt.get("failure_classification"),
                        "retryable": attempt.get("retryable"),
                    }
                )

    retry_count = receipt.get("retry_count", 0)
    report = {
        "schema_version": 1,
        "logical_route": receipt.get("logical_route"),
        "delivery_id": receipt.get("delivery_id"),
        "delivery_status": receipt.get("delivery_status"),
        "attempt_count": receipt.get("attempt_count", 0),
        "retry_count": retry_count,
        "terminal_http_status": receipt.get("http_status"),
        "terminal_failure_classification": receipt.get("failure_classification"),
        "transport_failure": receipt.get("failure_classification") == "transport_error",
        "had_retries": isinstance(retry_count, int) and retry_count > 0,
        "attempts": attempts,
        "external_export_enabled": False,
    }

    serialized = json.dumps(report, sort_keys=True).lower()
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment in serialized:
            raise ValueError(f"observability evidence contains forbidden material {fragment}")

    return report


def render_summary(report: dict[str, Any]) -> str:
    return (
        "\n".join(
            [
                "## Routed Delivery Observability",
                "",
                f"- Logical route: `{report.get('logical_route')}`",
                f"- Delivery status: `{report.get('delivery_status')}`",
                f"- Attempts: `{report.get('attempt_count')}`",
                f"- Retries: `{report.get('retry_count')}`",
                f"- Terminal HTTP status: `{report.get('terminal_http_status')}`",
                (
                    "- Terminal failure classification: "
                    f"`{report.get('terminal_failure_classification')}`"
                ),
                f"- Transport failure: `{report.get('transport_failure')}`",
                f"- Had retries: `{report.get('had_retries')}`",
            ]
        )
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--max-attempt-records", type=int, default=3)
    args = parser.parse_args()

    report = build_observability(
        _load_json(args.receipt),
        max_attempt_records=max(0, args.max_attempt_records),
    )

    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.summary.write_text(render_summary(report), encoding="utf-8")

    print(
        "recovery alert routed SLO alert delivery routed delivery "
        "routed delivery observability built"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
