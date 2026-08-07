"""Build secret-safe observability for routed recovery alert delivery."""

from __future__ import annotations

import argparse
import json
import statistics
import tomllib
from collections import Counter
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
    policy = alerting.get("routed_delivery_observability")
    if not isinstance(policy, dict):
        raise ValueError("alerting.routed_delivery_observability policy is missing")
    return policy


def _history_receipts(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    receipts: list[dict[str, Any]] = []
    for path in sorted(root.rglob("recovery-alert-routed-delivery.json")):
        try:
            receipts.append(_load_json(path))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return receipts


def _deduplicate(receipts: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for receipt in receipts:
        delivery_id = receipt.get("delivery_id")
        delivered_at = receipt.get("delivered_at")
        key = str(delivery_id) if delivery_id else f"no-id:{delivered_at}:{receipt.get('route')}"
        by_key[key] = receipt
    ordered = sorted(by_key.values(), key=lambda item: str(item.get("delivered_at", "")))
    return ordered[-limit:]


def _safe_float(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def build_observation(
    current: dict[str, Any],
    history: list[dict[str, Any]],
    policy: dict[str, Any],
) -> dict[str, Any]:
    history_limit = max(int(policy.get("history_limit", 52)), 1)
    sample = _deduplicate([*history, current], history_limit)
    required = [item for item in sample if bool(item.get("route_required"))]
    delivered = [item for item in required if bool(item.get("delivered"))]
    attempts = [int(item.get("attempts", 0)) for item in required]
    retries = [max(value - 1, 0) for value in attempts]
    route_counts = Counter(str(item.get("route", "unknown")) for item in required)
    failure_counts = Counter(str(item.get("failure_class") or "none") for item in required)
    latencies = [
        value
        for item in required
        if (value := _safe_float(item.get("elapsed_seconds"))) is not None
    ]
    total_attempts = sum(attempts)
    total_retries = sum(retries)

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "sample_count": len(required),
        "history_count": max(len(required) - 1, 0),
        "history_limit": history_limit,
        "current_route": current.get("route"),
        "current_severity": current.get("severity"),
        "current_delivered": bool(current.get("delivered")),
        "current_attempts": int(current.get("attempts", 0)),
        "success_count": len(delivered),
        "success_rate": len(delivered) / len(required) if required else 0.0,
        "total_attempts": total_attempts,
        "total_retries": total_retries,
        "retry_rate": total_retries / total_attempts if total_attempts else 0.0,
        "average_attempts": statistics.fmean(attempts) if attempts else 0.0,
        "max_attempts": max(attempts, default=0),
        "average_latency_seconds": statistics.fmean(latencies) if latencies else 0.0,
        "max_latency_seconds": max(latencies, default=0.0),
        "route_counts": dict(sorted(route_counts.items())),
        "failure_counts": dict(sorted(failure_counts.items())),
        "transport_failure_count": failure_counts.get("transport", 0),
        "terminal_http_failure_count": failure_counts.get("terminal-http", 0),
        "retryable_http_failure_count": failure_counts.get("retryable-http", 0),
    }


def render_summary(observation: dict[str, Any]) -> str:
    lines = [
        "## Routed Recovery Alert Delivery Observability",
        "",
        f"- Samples: {observation['sample_count']}",
        f"- Success rate: {observation['success_rate']:.2%}",
        f"- Retry rate: {observation['retry_rate']:.2%}",
        f"- Average attempts: {observation['average_attempts']:.2f}",
        f"- Maximum attempts: {observation['max_attempts']}",
        f"- Average latency: {observation['average_latency_seconds']:.3f}s",
        f"- Maximum latency: {observation['max_latency_seconds']:.3f}s",
        "",
        "### Routes",
        "",
    ]
    route_counts = observation["route_counts"]
    if route_counts:
        lines.extend(f"- {route}: {count}" for route, count in route_counts.items())
    else:
        lines.append("- No routed deliveries observed")

    lines.extend(["", "### Failure Classes", ""])
    failure_counts = observation["failure_counts"]
    if failure_counts:
        lines.extend(f"- {failure}: {count}" for failure, count in failure_counts.items())
    else:
        lines.append("- No failures observed")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--history-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    observation = build_observation(
        _load_json(args.receipt),
        _history_receipts(args.history_root),
        _load_policy(args.policy),
    )
    args.output.write_text(
        json.dumps(observation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.summary.write_text(render_summary(observation), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
