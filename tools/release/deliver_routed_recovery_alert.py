"""Deliver a routed recovery alert with route-specific signed webhooks."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


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


def deliver(
    route: dict[str, Any],
    alert: dict[str, Any],
    endpoint_url: str,
    hmac_secret: str,
    timeout_seconds: float = 10.0,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    started = time.monotonic()

    if not route.get("route_required"):
        return {
            "schema_version": 1,
            "delivered_at": datetime.now(UTC).isoformat(),
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "route_required": False,
            "delivered": False,
            "route": route.get("route", "none"),
            "severity": route.get("severity", "NONE"),
            "status_code": None,
            "delivery_id": None,
            "failure_class": None,
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

    request = urllib.request.Request(
        endpoint_url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "MusicClean-Orion-Routed-Recovery-Alert/1",
            "X-MusicClean-Route": route_name,
            "X-MusicClean-Delivery-ID": delivery_id,
            "X-MusicClean-Signature-SHA256": f"sha256={signature}",
        },
    )

    status_code: int | None = None
    failure_class: str | None = None

    try:
        response = opener(request, timeout=timeout_seconds)
        status_code = int(getattr(response, "status", 200))
        delivered = 200 <= status_code < 300
        if not delivered:
            failure_class = (
                "retryable-http" if status_code == 429 or status_code >= 500 else "terminal-http"
            )
    except urllib.error.HTTPError as exc:
        status_code = int(exc.code)
        delivered = False
        failure_class = (
            "retryable-http" if status_code == 429 or status_code >= 500 else "terminal-http"
        )
    except (OSError, TimeoutError, urllib.error.URLError):
        delivered = False
        failure_class = "transport"

    return {
        "schema_version": 1,
        "delivered_at": datetime.now(UTC).isoformat(),
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "route_required": True,
        "delivered": delivered,
        "route": route_name,
        "severity": route["severity"],
        "status_code": status_code,
        "delivery_id": delivery_id,
        "failure_class": failure_class,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--alert", type=Path, required=True)
    parser.add_argument("--endpoint-url", required=True)
    parser.add_argument("--hmac-secret", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    receipt = deliver(
        _load_json(args.route),
        _load_json(args.alert),
        args.endpoint_url,
        args.hmac_secret,
    )
    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.receipt)
    return 0 if receipt["delivered"] or not receipt["route_required"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
