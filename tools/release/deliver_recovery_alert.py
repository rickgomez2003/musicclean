"""Deliver a recovery SLO alert to a generic HTTPS webhook resiliently."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import time
import tomllib
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_delivery_policy(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)
    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("recovery alerting policy is missing")
    delivery = alerting.get("delivery")
    if not isinstance(delivery, dict):
        raise ValueError("recovery alert delivery policy is missing")
    return delivery


def _canonical_payload(alert: dict[str, Any]) -> bytes:
    return json.dumps(
        alert,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _signature(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _delivery_id(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _retryable_status(status_code: int, policy: dict[str, Any]) -> bool:
    configured = policy.get("retry_statuses")
    retry_statuses = {
        int(value) for value in configured
    } if isinstance(configured, list) else set()
    if status_code in retry_statuses:
        return True
    return bool(policy.get("retry_server_errors", True)) and 500 <= status_code < 600


def _backoff_seconds(attempt: int, policy: dict[str, Any]) -> float:
    initial = float(policy.get("initial_backoff_seconds", 1))
    maximum = float(policy.get("maximum_backoff_seconds", 8))
    return min(initial * (2 ** (attempt - 1)), maximum)


def deliver(
    *,
    alert: dict[str, Any],
    policy: dict[str, Any],
    webhook_url: str,
    hmac_secret: str,
    opener: Callable[..., Any] = urllib.request.urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    started_at = time.monotonic()

    if not alert.get("alert_required"):
        return {
            "schema_version": 2,
            "delivered_at": datetime.now(UTC).isoformat(),
            "elapsed_seconds": round(time.monotonic() - started_at, 6),
            "delivery_required": False,
            "delivered": False,
            "attempts": 0,
            "attempt_history": [],
            "status_code": None,
            "provider": "generic-webhook",
            "severity": alert.get("severity"),
            "delivery_id": None,
            "failure_class": None,
            "reason": "alert not required",
        }

    if policy.get("require_https") is True and not webhook_url.startswith("https://"):
        raise ValueError("recovery alert webhook URL must use HTTPS")

    payload = _canonical_payload(alert)
    delivery_id = _delivery_id(payload)

    idempotency_header = str(
        policy.get("idempotency_header", "X-MusicClean-Delivery-ID")
    )
    signature_header = str(
        policy.get(
            "signature_header",
            "X-MusicClean-Signature-SHA256",
        )
    )

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "MusicClean-Orion-Recovery-Alert/2",
        idempotency_header: delivery_id,
    }
    if policy.get("sign_payload") is True:
        if not hmac_secret:
            raise ValueError("HMAC signing secret is required")
        headers[signature_header] = _signature(payload, hmac_secret)

    max_attempts = int(policy["max_attempts"])
    timeout = float(policy["request_timeout_seconds"])
    attempt_history: list[dict[str, Any]] = []
    status_code: int | None = None
    failure_class: str | None = None
    reason: str | None = None

    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(
            webhook_url,
            data=payload,
            headers=headers,
            method="POST",
        )

        retryable = False
        try:
            with opener(request, timeout=timeout) as response:
                status_code = int(response.getcode())

            if 200 <= status_code < 300:
                attempt_history.append(
                    {
                        "attempt": attempt,
                        "status_code": status_code,
                        "outcome": "delivered",
                        "retryable": False,
                    }
                )
                return {
                    "schema_version": 2,
                    "delivered_at": datetime.now(UTC).isoformat(),
                    "elapsed_seconds": round(
                        time.monotonic() - started_at,
                        6,
                    ),
                    "delivery_required": True,
                    "delivered": True,
                    "attempts": attempt,
                    "attempt_history": attempt_history,
                    "status_code": status_code,
                    "provider": "generic-webhook",
                    "severity": alert.get("severity"),
                    "delivery_id": delivery_id,
                    "failure_class": None,
                    "reason": None,
                }

            retryable = _retryable_status(status_code, policy)
            failure_class = "transient-http" if retryable else "terminal-http"
            reason = f"HTTP {status_code}"
        except urllib.error.HTTPError as exc:
            status_code = int(exc.code)
            retryable = _retryable_status(status_code, policy)
            failure_class = "transient-http" if retryable else "terminal-http"
            reason = f"HTTP {status_code}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            retryable = True
            failure_class = "transient-network"
            reason = exc.__class__.__name__

        attempt_history.append(
            {
                "attempt": attempt,
                "status_code": status_code,
                "outcome": "failed",
                "retryable": retryable,
                "failure_class": failure_class,
            }
        )

        if not retryable or attempt >= max_attempts:
            break

        sleeper(_backoff_seconds(attempt, policy))

    return {
        "schema_version": 2,
        "delivered_at": datetime.now(UTC).isoformat(),
        "elapsed_seconds": round(time.monotonic() - started_at, 6),
        "delivery_required": True,
        "delivered": False,
        "attempts": len(attempt_history),
        "attempt_history": attempt_history,
        "status_code": status_code,
        "provider": "generic-webhook",
        "severity": alert.get("severity"),
        "delivery_id": delivery_id,
        "failure_class": failure_class,
        "reason": reason or "delivery failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--alert", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    policy = _load_delivery_policy(args.policy)
    alert = _load_json(args.alert)

    url_name = str(policy["url_secret"])
    hmac_name = str(policy["hmac_secret"])
    webhook_url = os.environ.get(url_name, "")
    hmac_secret = os.environ.get(hmac_name, "")

    if alert.get("alert_required") and not webhook_url:
        raise ValueError(f"required recovery alert secret {url_name} is not configured")

    receipt = deliver(
        alert=alert,
        policy=policy,
        webhook_url=webhook_url,
        hmac_secret=hmac_secret,
    )
    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.receipt)
    return 0 if (receipt["delivered"] or not receipt["delivery_required"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
