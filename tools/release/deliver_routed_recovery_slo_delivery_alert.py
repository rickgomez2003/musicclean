"""Deliver routed recovery SLO-delivery alerts with bounded retry resilience."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import time
import tomllib
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

Transport = Callable[[urllib.request.Request, float], int]
Sleeper = Callable[[float], None]


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_resilience_policy(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)
    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("alerting policy is missing")
    policy = alerting.get("routed_slo_alert_delivery_routed_delivery_resilience")
    if not isinstance(policy, dict):
        raise ValueError("routed SLO alert delivery routed-delivery resilience policy is missing")
    return policy


def _canonical_json(data: dict[str, Any]) -> bytes:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _delivery_id(route: dict[str, Any], alert: dict[str, Any]) -> str:
    seed = {
        "route": route.get("route"),
        "severity": route.get("severity"),
        "alert_delivery_id": alert.get("delivery_id"),
        "source_route": route.get("source_route"),
    }
    digest = hashlib.sha256(_canonical_json(seed)).hexdigest()
    return f"recovery-slo-delivery-{digest[:24]}"


def _default_transport(request: urllib.request.Request, timeout: float) -> int:
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return int(response.status)


def _backoff_delay(attempt: int, base: float, maximum: float) -> float:
    return min(maximum, base * (2 ** max(0, attempt - 1)))


def deliver(
    route: dict[str, Any],
    alert: dict[str, Any],
    *,
    endpoint_url: str | None,
    hmac_secret: str | None,
    timeout_seconds: float = 10.0,
    resilience: dict[str, Any] | None = None,
    transport: Transport | None = None,
    sleeper: Sleeper = time.sleep,
) -> dict[str, Any]:
    logical_route = str(route.get("route", "none"))
    delivery_id = _delivery_id(route, alert)

    policy = resilience or {}
    max_attempts = max(1, int(policy.get("max_attempts", 1)))
    base_delay = max(0.0, float(policy.get("base_delay_seconds", 0.0)))
    max_delay = max(base_delay, float(policy.get("max_delay_seconds", base_delay)))
    retryable_statuses = {int(value) for value in policy.get("retryable_http_statuses", [])}
    retry_transport_errors = bool(policy.get("retry_transport_errors", False))
    preserve_delivery_id = bool(policy.get("preserve_delivery_id", True))

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "delivery_id": delivery_id,
        "logical_route": logical_route,
        "severity": route.get("severity"),
        "delivered": False,
        "attempt_count": 0,
        "retry_count": 0,
        "attempts": [],
        "http_status": None,
        "failure_classification": None,
    }

    if logical_route == "none":
        receipt["failure_classification"] = "route_none"
        return receipt

    if logical_route not in {"operations", "incident-response"}:
        raise ValueError(f"unsupported logical route: {logical_route}")

    if not endpoint_url or not hmac_secret:
        receipt["failure_classification"] = "credentials_unavailable"
        return receipt

    parsed = urlparse(endpoint_url)
    if parsed.scheme.lower() != "https":
        raise ValueError("routed SLO alert delivery requires HTTPS")

    payload = {
        "schema_version": 1,
        "delivery_id": delivery_id,
        "logical_route": logical_route,
        "alert": alert,
    }
    body = _canonical_json(payload)
    signature = hmac.new(
        hmac_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    sender = transport or _default_transport

    for attempt in range(1, max_attempts + 1):
        request_delivery_id = (
            delivery_id
            if preserve_delivery_id
            else _delivery_id(
                {**route, "attempt": attempt},
                alert,
            )
        )
        request = urllib.request.Request(
            endpoint_url,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-MusicClean-Delivery-ID": request_delivery_id,
                "X-MusicClean-Signature": f"sha256={signature}",
            },
        )

        receipt["attempt_count"] = attempt
        attempt_record: dict[str, Any] = {
            "attempt": attempt,
            "http_status": None,
            "classification": None,
            "retryable": False,
        }

        try:
            status = int(sender(request, timeout_seconds))
            attempt_record["http_status"] = status
            receipt["http_status"] = status
            if 200 <= status < 300:
                receipt["delivered"] = True
                receipt["failure_classification"] = None
                attempt_record["classification"] = "success"
                receipt["attempts"].append(attempt_record)
                break

            retryable = status in retryable_statuses
            attempt_record["classification"] = "http_error"
            attempt_record["retryable"] = retryable
            receipt["failure_classification"] = "http_error"
            receipt["attempts"].append(attempt_record)

            if not retryable or attempt >= max_attempts:
                break

        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            attempt_record["http_status"] = status
            receipt["http_status"] = status
            retryable = status in retryable_statuses
            attempt_record["classification"] = "http_error"
            attempt_record["retryable"] = retryable
            receipt["failure_classification"] = "http_error"
            receipt["attempts"].append(attempt_record)

            if not retryable or attempt >= max_attempts:
                break

        except (urllib.error.URLError, TimeoutError, OSError):
            attempt_record["classification"] = "transport_error"
            attempt_record["retryable"] = retry_transport_errors
            receipt["failure_classification"] = "transport_error"
            receipt["attempts"].append(attempt_record)

            if not retry_transport_errors or attempt >= max_attempts:
                break

        receipt["retry_count"] += 1
        delay = _backoff_delay(attempt, base_delay, max_delay)
        if delay > 0:
            sleeper(delay)

    return receipt


def verify_receipt_secret_safe(receipt: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    serialized = json.dumps(receipt, sort_keys=True).lower()

    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
        "request_headers",
    ):
        if fragment in serialized:
            errors.append(f"delivery receipt contains forbidden material {fragment}")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--alert", type=Path, required=True)
    parser.add_argument("--endpoint-url")
    parser.add_argument("--hmac-secret")
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    receipt = deliver(
        _load_json(args.route),
        _load_json(args.alert),
        endpoint_url=args.endpoint_url,
        hmac_secret=args.hmac_secret,
        timeout_seconds=args.timeout_seconds,
        resilience=_load_resilience_policy(args.policy),
    )

    errors = verify_receipt_secret_safe(receipt)
    if errors:
        raise ValueError("; ".join(errors))

    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return 0 if receipt["delivered"] or receipt["logical_route"] == "none" else 1


if __name__ == "__main__":
    raise SystemExit(main())
