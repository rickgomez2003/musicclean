"""Build bounded, deduplicated history for routed-delivery SLO evidence."""

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


def _load_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")
    return [item for item in data if isinstance(item, dict)]


def _load_policy(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("alerting policy is missing")

    policy = alerting.get("routed_slo_alert_delivery_routed_delivery_slo_history")
    if not isinstance(policy, dict):
        raise ValueError("routed SLO alert delivery routed-delivery SLO history policy is missing")
    return policy


def _entry(report: dict[str, Any]) -> dict[str, Any]:
    metrics = report.get("metrics")
    if not isinstance(metrics, dict):
        metrics = {}

    return {
        "delivery_id": report.get("delivery_id"),
        "logical_route": report.get("logical_route"),
        "sample_count": report.get("sample_count"),
        "minimum_samples": report.get("minimum_samples"),
        "authoritative": report.get("authoritative"),
        "overall_classification": report.get("overall_classification"),
        "metrics": {
            name: {
                "value": value.get("value"),
                "classification": value.get("classification"),
            }
            for name, value in metrics.items()
            if isinstance(value, dict)
        },
    }


def build_history(
    report: dict[str, Any],
    existing: list[dict[str, Any]],
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    maximum = max(1, int(policy.get("max_records", 30)))
    current = _entry(report)

    delivery_id = current.get("delivery_id")
    if not isinstance(delivery_id, str) or not delivery_id:
        raise ValueError("SLO report must contain a non-empty delivery_id")

    deduplicated = [item for item in existing if item.get("delivery_id") != delivery_id]
    deduplicated.append(current)

    return deduplicated[-maximum:]


def verify_secret_safe(history: list[dict[str, Any]]) -> tuple[str, ...]:
    serialized = json.dumps(history, sort_keys=True).lower()
    errors: list[str] = []
    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
        "request_headers",
    ):
        if fragment in serialized:
            errors.append(f"SLO history contains forbidden material {fragment}")
    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--slo", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    args = parser.parse_args()

    report = _load_json(args.slo)
    existing = _load_history(args.history)
    history = build_history(report, existing, _load_policy(args.policy))

    errors = verify_secret_safe(history)
    if errors:
        raise ValueError("; ".join(errors))

    args.history.write_text(
        json.dumps(history, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
