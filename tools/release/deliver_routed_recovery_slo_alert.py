"""Deliver routed recovery SLO alerts using resilient signed webhooks."""

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

DEFAULT_RETRY_POLICY: dict[str, Any] = {
    "max_attempts": 3,
    "base_delay_seconds": 1.0,
    "max_delay_seconds": 4.0,
    "retryable_http_statuses": [408, 425, 429, 500, 502, 503, 504],
    "retry_transport_errors": True,
}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_retry_policy(path: Path | None) -> dict[str, Any]:
    if path is None:
        return dict(DEFAULT_RETRY_POLICY)
    with path.open("rb") as stream:
        document = tomllib.load(stream)
    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("alerting policy is missing")
    policy = alerting.get("routed_slo_alert_delivery_resilience")
    if not isinstance(policy, dict):
        raise ValueError("alerting.routed_slo_alert_delivery_resilience policy is missing")
    merged = dict(DEFAULT_RETRY_POLICY)
    merged.update(policy)
    return merged


def _canonical_payload(route: dict[str, Any], alert: dict[str, Any]) -> bytes:
    payload = {
        "schema_version": 1,
        "route": route.get("route"),
        "severity": route.get("severity"),
        "escalated": route.get("escalated"),
        "source_route": route.get("source_route"),
        "alert": {
            "alert_required": alert.get("alert_required"),
            "severity": alert.get("severity"),
            "escalated": alert.get("escalated"),
            "reasons": alert.get("reasons"),
            "current_status": alert.get("current_status"),
            "trend": alert.get("trend"),
            "consecutive_nonpass_count": alert.get("consecutive_nonpass_count"),
        },
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _delivery_id(route: dict[str, Any], payload: bytes) -> str:
    material = str(route.get("route", "none")).encode() + b"\0" + payload
    return "musicclean-routed-slo-" + hashlib.sha256(material).hexdigest()[:32]


def _delay(policy: dict[str, Any], attempt: int) -> float:
    base = max(float(policy.get("base_delay_seconds", 1.0)), 0.0)
    maximum = max(float(policy.get("max_delay_seconds", 4.0)), 0.0)
    return min(base * (2 ** max(attempt - 1, 0)), maximum)


def deliver(
    route: dict[str, Any],
    alert: dict[str, Any],
    endpoint_url: str,
    hmac_secret: str,
    *,
    retry_policy: dict[str, Any] | None = None,
    timeout_seconds: float = 10.0,
    opener: Any = urllib.request.urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    logical_route = str(route.get("route", "none"))
    if logical_route == "none" or not bool(route.get("route_required")):
        return {
            "schema_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "delivery_id": None,
            "route": logical_route,
            "attempted": False,
            "delivered": False,
            "status": "NOT_REQUIRED",
            "http_status": None,
            "failure_class": None,
            "attempt_count": 0,
            "attempt_history": [],
        }

    if urlparse(endpoint_url).scheme != "https":
        raise ValueError("routed SLO alert delivery requires HTTPS")
    if not hmac_secret:
        raise ValueError("routed SLO alert delivery HMAC secret is required")

    policy = dict(DEFAULT_RETRY_POLICY)
    if retry_policy:
        policy.update(retry_policy)
    max_attempts = max(int(policy.get("max_attempts", 3)), 1)
    retryable_http = {int(v) for v in policy.get("retryable_http_statuses", [])}
    retry_transport = bool(policy.get("retry_transport_errors", True))

    body = _canonical_payload(route, alert)
    signature = hmac.new(hmac_secret.encode(), body, hashlib.sha256).hexdigest()
    delivery_id = _delivery_id(route, body)
    request = urllib.request.Request(
        endpoint_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "MusicClean-Orion-Routed-SLO-Alert/2",
            "X-MusicClean-Delivery-ID": delivery_id,
            "X-MusicClean-Route": logical_route,
            "X-MusicClean-Signature-SHA256": f"sha256={signature}",
        },
    )

    attempts = []
    final_status = None
    final_failure = None

    for attempt in range(1, max_attempts + 1):
        delivered = False
        http_status = None
        raw_failure = None
        try:
            response = opener(request, timeout=timeout_seconds)
            http_status = int(response.getcode())
            delivered = 200 <= http_status < 300
        except urllib.error.HTTPError as exc:
            http_status = int(exc.code)
            raw_failure = "HTTP"
        except (OSError, urllib.error.URLError):
            raw_failure = "TRANSPORT"

        final_status = http_status
        if delivered:
            attempts.append(
                {
                    "attempt": attempt,
                    "delivered": True,
                    "http_status": http_status,
                    "failure_class": None,
                }
            )
            return {
                "schema_version": 1,
                "generated_at": datetime.now(UTC).isoformat(),
                "delivery_id": delivery_id,
                "route": logical_route,
                "attempted": True,
                "delivered": True,
                "status": "DELIVERED",
                "http_status": http_status,
                "failure_class": None,
                "attempt_count": attempt,
                "attempt_history": attempts,
            }

        if raw_failure == "TRANSPORT":
            failure_class, retryable = "TRANSPORT", retry_transport
        elif http_status in retryable_http:
            failure_class, retryable = "RETRYABLE_HTTP", True
        else:
            failure_class, retryable = "TERMINAL_HTTP", False

        final_failure = failure_class
        attempts.append(
            {
                "attempt": attempt,
                "delivered": False,
                "http_status": http_status,
                "failure_class": failure_class,
            }
        )
        if not retryable or attempt >= max_attempts:
            break
        sleeper(_delay(policy, attempt))

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "delivery_id": delivery_id,
        "route": logical_route,
        "attempted": True,
        "delivered": False,
        "status": "FAILED",
        "http_status": final_status,
        "failure_class": final_failure,
        "attempt_count": len(attempts),
        "attempt_history": attempts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--alert", type=Path, required=True)
    parser.add_argument("--endpoint-url", required=True)
    parser.add_argument("--hmac-secret", required=True)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    receipt = deliver(
        _load_json(args.route),
        _load_json(args.alert),
        args.endpoint_url,
        args.hmac_secret,
        retry_policy=_load_retry_policy(args.policy),
    )
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
