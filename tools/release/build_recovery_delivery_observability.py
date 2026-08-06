"""Build recovery alert delivery observability evidence."""

from __future__ import annotations

import argparse
import json
import statistics
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
        raise ValueError("recovery alerting policy is missing")
    observability = alerting.get("observability")
    if not isinstance(observability, dict):
        raise ValueError("recovery alert observability policy is missing")
    return observability


def _collect_history(root: Path, limit: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not root.exists():
        return records

    for path in sorted(root.rglob("recovery-alert-delivery.json")):
        try:
            record = _load_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        records.append(record)

    records.sort(key=lambda item: str(item.get("delivered_at", "")))
    return records[-limit:]


def _latency_seconds(receipt: dict[str, Any]) -> float | None:
    value = receipt.get("elapsed_seconds")
    if isinstance(value, (int, float)) and value >= 0:
        return float(value)
    return None


def build(
    *,
    receipt: dict[str, Any],
    history: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    combined = [*history, receipt]
    delivered = [item for item in combined if item.get("delivered") is True]
    required = [item for item in combined if item.get("delivery_required") is True]

    attempts = int(receipt.get("attempts", 0))
    retry_count = max(attempts - 1, 0)

    aggregate_attempt_count = sum(int(item.get("attempts", 0)) for item in required)
    aggregate_retry_count = sum(max(int(item.get("attempts", 0)) - 1, 0) for item in required)
    retry_rate = (
        aggregate_retry_count / aggregate_attempt_count if aggregate_attempt_count > 0 else 0.0
    )

    terminal_failure_count = sum(
        1 for item in required if item.get("failure_class") == "terminal-http"
    )
    terminal_failure_rate = terminal_failure_count / len(required) if required else 0.0

    latencies = [latency for item in combined if (latency := _latency_seconds(item)) is not None]

    success_rate = len(delivered) / len(required) if required else 1.0

    return {
        "schema_version": int(policy["schema_version"]),
        "generated_at": datetime.now(UTC).isoformat(),
        "delivery_id": receipt.get("delivery_id"),
        "delivery_required": receipt.get("delivery_required"),
        "delivered": receipt.get("delivered"),
        "attempt_count": attempts,
        "retry_count": retry_count,
        "aggregate_attempt_count": aggregate_attempt_count,
        "aggregate_retry_count": aggregate_retry_count,
        "retry_rate": retry_rate,
        "terminal_failure_count": terminal_failure_count,
        "terminal_failure_rate": terminal_failure_rate,
        "status_code": receipt.get("status_code"),
        "failure_class": receipt.get("failure_class"),
        "provider": receipt.get("provider"),
        "sample_count": len(combined),
        "required_sample_count": len(required),
        "delivered_sample_count": len(delivered),
        "success_rate": success_rate,
        "average_latency_seconds": (statistics.fmean(latencies) if latencies else None),
        "maximum_latency_seconds": max(latencies) if latencies else None,
        "history_limit": int(policy["history_limit"]),
    }


def render_summary(observation: dict[str, Any]) -> str:
    delivered = "yes" if observation.get("delivered") else "no"
    failure_class = observation.get("failure_class") or "none"
    status_code = observation.get("status_code")
    success_rate = float(observation["success_rate"]) * 100.0

    return (
        "## Recovery Alert Delivery Observability\n\n"
        f"- Delivery ID: `{observation.get('delivery_id')}`\n"
        f"- Delivered: **{delivered}**\n"
        f"- Attempts: **{observation.get('attempt_count')}**\n"
        f"- Retries: **{observation.get('retry_count')}**\n"
        f"- Status code: **{status_code}**\n"
        f"- Failure class: **{failure_class}**\n"
        f"- Historical samples: **{observation.get('sample_count')}**\n"
        f"- Delivery success rate: **{success_rate:.1f}%**\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--history-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    policy = _load_policy(args.policy)
    receipt = _load_json(args.receipt)
    history = _collect_history(
        args.history_root,
        int(policy["history_limit"]),
    )
    observation = build(
        receipt=receipt,
        history=history,
        policy=policy,
    )

    args.output.write_text(
        json.dumps(observation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.summary.write_text(
        render_summary(observation),
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
