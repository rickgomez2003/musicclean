"""Deliver routed recovery SLO-delivery alerts to route-specific signed webhooks."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

Transport = Callable[[urllib.request.Request, float], int]


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


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


def deliver(
    route: dict[str, Any],
    alert: dict[str, Any],
    *,
    endpoint_url: str | None,
    hmac_secret: str | None,
    timeout_seconds: float = 10.0,
    transport: Transport | None = None,
) -> dict[str, Any]:
    logical_route = str(route.get("route", "none"))
    delivery_id = _delivery_id(route, alert)

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "delivery_id": delivery_id,
        "logical_route": logical_route,
        "severity": route.get("severity"),
        "delivered": False,
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

    request = urllib.request.Request(
        endpoint_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-MusicClean-Delivery-ID": delivery_id,
            "X-MusicClean-Signature": f"sha256={signature}",
        },
    )

    sender = transport or _default_transport
    try:
        status = sender(request, timeout_seconds)
    except urllib.error.HTTPError as exc:
        receipt["http_status"] = int(exc.code)
        receipt["failure_classification"] = "http_error"
        return receipt
    except (urllib.error.URLError, TimeoutError, OSError):
        receipt["failure_classification"] = "transport_error"
        return receipt

    receipt["http_status"] = int(status)
    if 200 <= int(status) < 300:
        receipt["delivered"] = True
    else:
        receipt["failure_classification"] = "http_error"

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
