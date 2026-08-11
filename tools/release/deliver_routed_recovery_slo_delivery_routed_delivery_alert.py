"""Deliver routed recovery SLO alert-delivery routed-delivery evidence."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROUTE_ENV = {
    "operations": (
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_OPERATIONS_URL",
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_OPERATIONS_HMAC_SECRET",
    ),
    "incident-response": (
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_INCIDENT_URL",
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_INCIDENT_HMAC_SECRET",
    ),
}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _canonical_payload(route: dict[str, Any]) -> bytes:
    payload = {
        "schema_version": 1,
        "delivery_id": route.get("delivery_id"),
        "logical_route": route.get("logical_route"),
        "route_reason": route.get("route_reason"),
        "source_alert_severity": route.get("source_alert_severity"),
        "source_alert_escalated": route.get("source_alert_escalated"),
        "source_alert_authoritative": route.get("source_alert_authoritative"),
    }
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _delivery_id(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _receipt(
    *,
    route: str,
    status: str,
    delivery_id: str,
    http_status: int | None = None,
    failure_classification: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "logical_route": route,
        "delivery_id": delivery_id,
        "delivery_status": status,
        "http_status": http_status,
        "failure_classification": failure_classification,
    }


def deliver(
    route: dict[str, Any],
    *,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    logical_route = str(route.get("logical_route", "none"))
    payload = _canonical_payload(route)
    delivery_id = _delivery_id(payload)

    if logical_route == "none":
        return _receipt(
            route=logical_route,
            status="NOT_REQUIRED",
            delivery_id=delivery_id,
        )

    env_names = ROUTE_ENV.get(logical_route)
    if env_names is None:
        return _receipt(
            route=logical_route,
            status="FAILED",
            delivery_id=delivery_id,
            failure_classification="unsupported_route",
        )

    url = os.environ.get(env_names[0], "")
    secret = os.environ.get(env_names[1], "")

    if not url or not secret:
        return _receipt(
            route=logical_route,
            status="FAILED",
            delivery_id=delivery_id,
            failure_classification="missing_credentials",
        )

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() != "https":
        return _receipt(
            route=logical_route,
            status="FAILED",
            delivery_id=delivery_id,
            failure_classification="insecure_endpoint",
        )

    signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "MusicClean-Orion/0.6.76",
            "X-Orion-Delivery-Id": delivery_id,
            "X-Orion-Signature-SHA256": signature,
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout_seconds,
        ) as response:
            status_code = int(response.status)
    except urllib.error.HTTPError as exc:
        return _receipt(
            route=logical_route,
            status="FAILED",
            delivery_id=delivery_id,
            http_status=int(exc.code),
            failure_classification="http_error",
        )
    except (urllib.error.URLError, TimeoutError, OSError):
        return _receipt(
            route=logical_route,
            status="FAILED",
            delivery_id=delivery_id,
            failure_classification="transport_error",
        )

    if 200 <= status_code < 300:
        return _receipt(
            route=logical_route,
            status="DELIVERED",
            delivery_id=delivery_id,
            http_status=status_code,
        )

    return _receipt(
        route=logical_route,
        status="FAILED",
        delivery_id=delivery_id,
        http_status=status_code,
        failure_classification="unexpected_http_status",
    )


def verify_secret_safe(receipt: dict[str, Any]) -> tuple[str, ...]:
    serialized = json.dumps(receipt, sort_keys=True).lower()
    errors: list[str] = []
    for fragment in (
        "endpoint_url",
        "hmac_secret",
        "signature",
        "authorization",
        "webhook_url",
        "request_headers",
        "https://",
        "http://",
    ):
        if fragment in serialized:
            errors.append(f"routed-delivery receipt contains forbidden material {fragment}")
    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    args = parser.parse_args()

    receipt = deliver(
        _load_json(args.route),
        timeout_seconds=args.timeout_seconds,
    )

    errors = verify_secret_safe(receipt)
    if errors:
        raise ValueError("; ".join(errors))

    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        f"routed recovery SLO alert delivery routed delivery result: {receipt['delivery_status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
