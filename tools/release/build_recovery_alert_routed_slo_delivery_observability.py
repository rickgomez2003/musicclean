from __future__ import annotations

import argparse
import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_policy(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        doc = tomllib.load(stream)
    alerting = doc.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("alerting policy is missing")
    policy = alerting.get("routed_slo_alert_delivery_observability")
    if not isinstance(policy, dict):
        raise ValueError("routed SLO observability policy is missing")
    return policy


def build_observability(receipt: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    history = receipt.get("attempt_history")
    attempts = history if isinstance(history, list) else []
    count = int(receipt.get("attempt_count", len(attempts)) or 0)
    max_records = int(policy.get("max_attempt_records", 10))
    statuses = [
        int(item["http_status"])
        for item in attempts
        if isinstance(item, dict) and isinstance(item.get("http_status"), int)
    ][-max_records:]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "delivery_id": receipt.get("delivery_id"),
        "route": receipt.get("route"),
        "status": receipt.get("status"),
        "metrics": {
            "attempted": bool(receipt.get("attempted")),
            "delivered": bool(receipt.get("delivered")),
            "attempt_count": count,
            "retry_count": max(count - 1, 0),
            "http_status": receipt.get("http_status"),
            "failure_class": receipt.get("failure_class"),
        },
        "attempt_statuses": statuses,
        "external_export_enabled": bool(policy.get("external_export_enabled", False)),
    }


def render_summary(report: dict[str, Any]) -> str:
    m = report["metrics"]
    return (
        "## Routed SLO Alert Delivery Observability\n\n"
        f"- Route: {report.get('route')}\n"
        f"- Status: {report.get('status')}\n"
        f"- Attempted: {str(m['attempted']).lower()}\n"
        f"- Delivered: {str(m['delivered']).lower()}\n"
        f"- Attempts: {m['attempt_count']}\n"
        f"- Retries: {m['retry_count']}\n"
        f"- HTTP status: {m['http_status']}\n"
        f"- Failure class: {m['failure_class']}\n"
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    a = p.parse_args()
    report = build_observability(load_json(a.receipt), load_policy(a.policy))
    a.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    a.summary.write_text(render_summary(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
