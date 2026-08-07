"""Deliver a routed recovery alert with route-specific signed webhooks."""

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
    "max_attempts": 1,
    "initial_backoff_seconds": 1.0,
    "backoff_multiplier": 2.0,
    "max_backoff_seconds": 8.0,
    "retry_server_errors": True,
    "retry_status_codes": [408, 425, 429],
    "retry_transport_errors": True,
}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_retry_policy(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("alerting policy is missing")

    policy = alerting.get("routed_delivery_resilience")
    if not isinstance(policy, dict):
        raise ValueError("alerting.routed_delivery_resilience policy is missing")

    return policy


def _require_https(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("routed recovery alert endpoint must use HTTPS")


def _canonical_payload(
    route: dict[str, Any],
    alert: dict[str, Any],
) -> bytes:
    body = {
        "schema_version": 1,
        "route": route["route"],
        "severity": route["severity"],
        "escalation_required": route["escalation_required"],
        "reasons": route.get("reasons", []),
        "alert": alert,
    }
    return json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _delivery_id(payload: bytes, route: str) -> str:
    digest = hashlib.sha256(route.encode("utf-8") + b"\0" + payload).hexdigest()
    return f"musicclean-routed-{digest[:32]}"


def _retryable_status(status_code: int, policy: dict[str, Any]) -> bool:
    retry_status_codes = {int(value) for value in policy.get("retry_status_codes", [])}
    if status_code in retry_status_codes:
        return True
    return bool(policy.get("retry_server_errors", True)) and 500 <= status_code < 600


def _backoff_seconds(attempt: int, policy: dict[str, Any]) -> float:
    initial = float(policy.get("initial_backoff_seconds", 1.0))
    multiplier = float(policy.get("backoff_multiplier", 2.0))
    maximum = float(policy.get("max_backoff_seconds", 8.0))
    return min(initial * (multiplier ** max(attempt - 1, 0)), maximum)


def deliver(
    route: dict[str, Any],
    alert: dict[str, Any],
    endpoint_url: str,
    hmac_secret: str,
    timeout_seconds: float = 10.0,
    retry_policy: dict[str, Any] | None = None,
    opener: Callable[..., Any] = urllib.request.urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    started = time.monotonic()
    policy = dict(DEFAULT_RETRY_POLICY)
    if retry_policy is not None:
        policy.update(retry_policy)

    if not route.get("route_required"):
        return {
            "schema_version": 2,
            "delivered_at": datetime.now(UTC).isoformat(),
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "route_required": False,
            "delivered": False,
            "route": route.get("route", "none"),
            "severity": route.get("severity", "NONE"),
            "status_code": None,
            "delivery_id": None,
            "failure_class": None,
            "attempts": 0,
            "attempt_history": [],
        }

    route_name = str(route["route"])
    _require_https(endpoint_url)

    payload = _canonical_payload(route, alert)
    signature = hmac.new(
        hmac_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    delivery_id = _delivery_id(payload, route_name)

    max_attempts = max(int(policy.get("max_attempts", 1)), 1)
    attempt_history: list[dict[str, Any]] = []

    delivered = False
    status_code: int | None = None
    failure_class: str | None = None

    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(
            endpoint_url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "MusicClean-Orion-Routed-Recovery-Alert/2",
                "X-MusicClean-Route": route_name,
                "X-MusicClean-Delivery-ID": delivery_id,
                "X-MusicClean-Attempt": str(attempt),
                "X-MusicClean-Signature-SHA256": f"sha256={signature}",
            },
        )

        retryable = False
        status_code = None
        failure_class = None

        try:
            response = opener(request, timeout=timeout_seconds)
            status_code = int(getattr(response, "status", 200))
            delivered = 200 <= status_code < 300
            if not delivered:
                retryable = _retryable_status(status_code, policy)
                failure_class = "retryable-http" if retryable else "terminal-http"
        except urllib.error.HTTPError as exc:
            status_code = int(exc.code)
            delivered = False
            retryable = _retryable_status(status_code, policy)
            failure_class = "retryable-http" if retryable else "terminal-http"
        except (OSError, TimeoutError, urllib.error.URLError):
            delivered = False
            retryable = bool(policy.get("retry_transport_errors", True))
            failure_class = "transport"

        attempt_history.append(
            {
                "attempt": attempt,
                "status_code": status_code,
                "delivered": delivered,
                "failure_class": failure_class,
                "retryable": retryable,
            }
        )

        if delivered or not retryable or attempt >= max_attempts:
            break

        sleeper(_backoff_seconds(attempt, policy))

    return {
        "schema_version": 2,
        "delivered_at": datetime.now(UTC).isoformat(),
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "route_required": True,
        "delivered": delivered,
        "route": route_name,
        "severity": route["severity"],
        "status_code": status_code,
        "delivery_id": delivery_id,
        "failure_class": failure_class,
        "attempts": len(attempt_history),
        "attempt_history": attempt_history,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--alert", type=Path, required=True)
    parser.add_argument("--endpoint-url", required=True)
    parser.add_argument("--hmac-secret", required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    retry_policy = _load_retry_policy(args.policy)
    receipt = deliver(
        _load_json(args.route),
        _load_json(args.alert),
        args.endpoint_url,
        args.hmac_secret,
        retry_policy=retry_policy,
    )
    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.receipt)
    return 0 if receipt["delivered"] or not receipt["route_required"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
