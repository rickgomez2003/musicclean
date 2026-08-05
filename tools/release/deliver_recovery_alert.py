"""Deliver a recovery SLO alert to a generic HTTPS webhook."""

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


def _signature(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def deliver(
    *,
    alert: dict[str, Any],
    policy: dict[str, Any],
    webhook_url: str,
    hmac_secret: str,
    opener: Callable[..., Any] = urllib.request.urlopen,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    if not alert.get("alert_required"):
        return {
            "schema_version": 1,
            "delivered_at": datetime.now(UTC).isoformat(),
            "delivery_required": False,
            "delivered": False,
            "attempts": 0,
            "status_code": None,
            "provider": "generic-webhook",
            "severity": alert.get("severity"),
            "reason": "alert not required",
        }

    if policy.get("require_https") is True and not webhook_url.startswith("https://"):
        raise ValueError("recovery alert webhook URL must use HTTPS")

    payload = json.dumps(
        alert,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "MusicClean-Orion-Recovery-Alert/1",
    }
    if policy.get("sign_payload") is True:
        if not hmac_secret:
            raise ValueError("HMAC signing secret is required")
        headers["X-MusicClean-Signature-SHA256"] = _signature(payload, hmac_secret)

    max_attempts = int(policy["max_attempts"])
    timeout = float(policy["request_timeout_seconds"])
    last_error: str | None = None
    status_code: int | None = None

    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(
            webhook_url,
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with opener(request, timeout=timeout) as response:
                status_code = int(response.getcode())
            if 200 <= status_code < 300:
                return {
                    "schema_version": 1,
                    "delivered_at": datetime.now(UTC).isoformat(),
                    "delivery_required": True,
                    "delivered": True,
                    "attempts": attempt,
                    "status_code": status_code,
                    "provider": "generic-webhook",
                    "severity": alert.get("severity"),
                    "reason": None,
                }
            last_error = f"unexpected HTTP status {status_code}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc.__class__.__name__

        if attempt < max_attempts:
            sleeper(float(attempt))

    return {
        "schema_version": 1,
        "delivered_at": datetime.now(UTC).isoformat(),
        "delivery_required": True,
        "delivered": False,
        "attempts": max_attempts,
        "status_code": status_code,
        "provider": "generic-webhook",
        "severity": alert.get("severity"),
        "reason": last_error or "delivery failed",
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
