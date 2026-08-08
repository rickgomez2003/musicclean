"""Deliver routed recovery SLO alerts using route-specific signed webhooks."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


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
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _delivery_id(route: dict[str, Any], payload: bytes) -> str:
    material = str(route.get("route", "none")).encode("utf-8") + b"\0" + payload
    digest = hashlib.sha256(material).hexdigest()[:32]
    return f"musicclean-routed-slo-{digest}"


def deliver(
    route: dict[str, Any],
    alert: dict[str, Any],
    endpoint_url: str,
    hmac_secret: str,
    *,
    timeout_seconds: float = 10.0,
    opener: Any = urllib.request.urlopen,
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
        }

    parsed = urlparse(endpoint_url)
    if parsed.scheme != "https":
        raise ValueError("routed SLO alert delivery requires HTTPS")

    if not hmac_secret:
        raise ValueError("routed SLO alert delivery HMAC secret is required")

    body = _canonical_payload(route, alert)
    signature = hmac.new(
        hmac_secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    delivery_id = _delivery_id(route, body)

    request = urllib.request.Request(
        endpoint_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "MusicClean-Orion-Routed-SLO-Alert/1",
            "X-MusicClean-Delivery-ID": delivery_id,
            "X-MusicClean-Route": logical_route,
            "X-MusicClean-Signature-SHA256": f"sha256={signature}",
        },
    )

    try:
        response = opener(request, timeout=timeout_seconds)
        status = int(response.getcode())
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        failure_class = (
            "RETRYABLE_HTTP" if status in {408, 425, 429, 500, 502, 503, 504} else "TERMINAL_HTTP"
        )
        return {
            "schema_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "delivery_id": delivery_id,
            "route": logical_route,
            "attempted": True,
            "delivered": False,
            "status": "FAILED",
            "http_status": status,
            "failure_class": failure_class,
        }
    except (OSError, urllib.error.URLError):
        return {
            "schema_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "delivery_id": delivery_id,
            "route": logical_route,
            "attempted": True,
            "delivered": False,
            "status": "FAILED",
            "http_status": None,
            "failure_class": "TRANSPORT",
        }

    delivered = 200 <= status < 300
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "delivery_id": delivery_id,
        "route": logical_route,
        "attempted": True,
        "delivered": delivered,
        "status": "DELIVERED" if delivered else "FAILED",
        "http_status": status,
        "failure_class": None if delivered else "TERMINAL_HTTP",
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
