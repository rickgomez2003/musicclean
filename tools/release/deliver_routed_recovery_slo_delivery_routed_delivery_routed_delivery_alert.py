from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROUTE_ENV = {
    "operations": (
        "ORION_ROUTED_SLO_OPERATIONS_WEBHOOK_URL",
        "ORION_ROUTED_SLO_OPERATIONS_HMAC_SECRET",
    ),
    "incident_response": (
        "ORION_ROUTED_SLO_INCIDENT_WEBHOOK_URL",
        "ORION_ROUTED_SLO_INCIDENT_HMAC_SECRET",
    ),
}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _canonical_json(document: dict[str, Any]) -> bytes:
    return json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _delivery_id(route: str, payload: dict[str, Any]) -> str:
    material = route.encode("utf-8") + b"\0" + _canonical_json(payload)
    return hashlib.sha256(material).hexdigest()


def _signed_request(
    *,
    url: str,
    secret: str,
    route: str,
    delivery_id: str,
    payload: dict[str, Any],
) -> urllib.request.Request:
    if not url.lower().startswith("https://"):
        raise ValueError("routed delivery requires HTTPS")

    body = _canonical_json(payload)
    signature = hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    return urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "musicclean-orion-routed-slo-delivery/1",
            "X-Orion-Route": route,
            "X-Orion-Delivery-Id": delivery_id,
            "X-Orion-Signature": f"sha256={signature}",
        },
    )


def deliver(
    route_report: dict[str, Any],
    *,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    logical_route = route_report.get("logical_route")

    base_receipt: dict[str, Any] = {
        "schema_version": 1,
        "logical_route": logical_route,
        "delivery_attempted": False,
        "delivered": False,
        "delivery_id": None,
        "http_status": None,
        "failure_classification": None,
        "provider_neutral": True,
    }

    if logical_route == "none":
        return {
            **base_receipt,
            "failure_classification": "not_required",
        }

    if logical_route not in ROUTE_ENV:
        return {
            **base_receipt,
            "failure_classification": "unsupported_route",
        }

    url_env, secret_env = ROUTE_ENV[logical_route]
    url = os.environ.get(url_env)
    secret = os.environ.get(secret_env)

    if not url or not secret:
        return {
            **base_receipt,
            "failure_classification": "missing_credentials",
        }

    payload = {
        "schema_version": 1,
        "logical_route": logical_route,
        "alert_state": route_report.get("alert_state"),
        "severity": route_report.get("severity"),
        "route_reason": route_report.get("route_reason"),
        "slo_authoritative": route_report.get("slo_authoritative"),
    }
    delivery_id = _delivery_id(logical_route, payload)

    try:
        request = _signed_request(
            url=url,
            secret=secret,
            route=logical_route,
            delivery_id=delivery_id,
            payload=payload,
        )
    except ValueError:
        return {
            **base_receipt,
            "delivery_id": delivery_id,
            "failure_classification": "insecure_endpoint",
        }

    receipt = {
        **base_receipt,
        "delivery_attempted": True,
        "delivery_id": delivery_id,
    }

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout_seconds,
        ) as response:
            status = int(response.getcode())

        return {
            **receipt,
            "delivered": 200 <= status < 300,
            "http_status": status,
            "failure_classification": (None if 200 <= status < 300 else "http_error"),
        }
    except urllib.error.HTTPError as exc:
        return {
            **receipt,
            "http_status": int(exc.code),
            "failure_classification": "http_error",
        }
    except (urllib.error.URLError, TimeoutError, OSError):
        return {
            **receipt,
            "failure_classification": "transport_error",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    args = parser.parse_args()

    receipt = deliver(
        _load_json(args.route),
        timeout_seconds=max(0.1, args.timeout_seconds),
    )

    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        "recovery alert routed SLO alert delivery routed delivery "
        "routed delivery routed delivery receipt written"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
