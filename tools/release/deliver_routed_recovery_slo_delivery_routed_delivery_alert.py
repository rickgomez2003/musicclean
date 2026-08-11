"""Deliver routed recovery SLO alert-delivery routed-delivery evidence."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import time
import tomllib
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


def _load_resilience_policy(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        raise ValueError("alerting policy is missing")

    policy = alerting.get("routed_slo_alert_delivery_routed_delivery_routed_delivery_resilience")
    if not isinstance(policy, dict):
        raise ValueError("routed-delivery resilience policy is missing")

    return policy


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
    attempts: list[dict[str, Any]],
    http_status: int | None = None,
    failure_classification: str | None = None,
) -> dict[str, Any]:
    attempt_count = len(attempts)
    return {
        "schema_version": 2,
        "logical_route": route,
        "delivery_id": delivery_id,
        "delivery_status": status,
        "attempt_count": attempt_count,
        "retry_count": max(0, attempt_count - 1),
        "attempts": attempts,
        "http_status": http_status,
        "failure_classification": failure_classification,
    }


def _backoff_seconds(
    attempt_number: int,
    *,
    initial: float,
    maximum: float,
) -> float:
    return min(maximum, initial * (2 ** max(0, attempt_number - 1)))


def deliver(
    route: dict[str, Any],
    *,
    timeout_seconds: float = 10.0,
    resilience_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    logical_route = str(route.get("logical_route", "none"))
    payload = _canonical_payload(route)
    delivery_id = _delivery_id(payload)

    policy = resilience_policy or {
        "max_attempts": 1,
        "initial_backoff_seconds": 0.0,
        "max_backoff_seconds": 0.0,
        "retry_transport_errors": False,
        "retry_http_statuses": [],
        "preserve_delivery_id": True,
        "max_attempt_records": 1,
    }

    max_attempts = max(1, int(policy.get("max_attempts", 1)))
    initial_backoff = max(0.0, float(policy.get("initial_backoff_seconds", 0.0)))
    max_backoff = max(0.0, float(policy.get("max_backoff_seconds", initial_backoff)))
    retry_transport_errors = bool(policy.get("retry_transport_errors", False))
    retry_http_statuses = {int(v) for v in policy.get("retry_http_statuses", [])}
    max_attempt_records = max(0, int(policy.get("max_attempt_records", max_attempts)))

    if logical_route == "none":
        return _receipt(
            route=logical_route,
            status="NOT_REQUIRED",
            delivery_id=delivery_id,
            attempts=[],
        )

    env_names = ROUTE_ENV.get(logical_route)
    if env_names is None:
        return _receipt(
            route=logical_route,
            status="FAILED",
            delivery_id=delivery_id,
            attempts=[],
            failure_classification="unsupported_route",
        )

    url = os.environ.get(env_names[0], "")
    secret = os.environ.get(env_names[1], "")
    if not url or not secret:
        return _receipt(
            route=logical_route,
            status="FAILED",
            delivery_id=delivery_id,
            attempts=[],
            failure_classification="missing_credentials",
        )

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() != "https":
        return _receipt(
            route=logical_route,
            status="FAILED",
            delivery_id=delivery_id,
            attempts=[],
            failure_classification="insecure_endpoint",
        )

    signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    attempts: list[dict[str, Any]] = []
    terminal_http_status: int | None = None
    terminal_failure: str | None = None

    for attempt_number in range(1, max_attempts + 1):
        request = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "MusicClean-Orion/0.6.77",
                "X-Orion-Delivery-Id": delivery_id,
                "X-Orion-Signature-SHA256": signature,
            },
        )

        retryable = False
        attempt_status = "FAILED"
        http_status: int | None = None
        failure_classification: str | None = None

        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                http_status = int(response.status)
                if 200 <= http_status < 300:
                    attempt_status = "DELIVERED"
                else:
                    failure_classification = "unexpected_http_status"
                    retryable = http_status in retry_http_statuses
        except urllib.error.HTTPError as exc:
            http_status = int(exc.code)
            failure_classification = "http_error"
            retryable = http_status in retry_http_statuses
        except (urllib.error.URLError, TimeoutError, OSError):
            failure_classification = "transport_error"
            retryable = retry_transport_errors

        terminal_http_status = http_status
        terminal_failure = failure_classification

        record = {
            "attempt": attempt_number,
            "delivery_id": delivery_id,
            "status": attempt_status,
            "http_status": http_status,
            "failure_classification": failure_classification,
            "retryable": retryable,
        }
        if len(attempts) < max_attempt_records:
            attempts.append(record)

        if attempt_status == "DELIVERED":
            return _receipt(
                route=logical_route,
                status="DELIVERED",
                delivery_id=delivery_id,
                attempts=attempts,
                http_status=http_status,
            )

        if not retryable or attempt_number >= max_attempts:
            break

        time.sleep(
            _backoff_seconds(
                attempt_number,
                initial=initial_backoff,
                maximum=max_backoff,
            )
        )

    return _receipt(
        route=logical_route,
        status="FAILED",
        delivery_id=delivery_id,
        attempts=attempts,
        http_status=terminal_http_status,
        failure_classification=terminal_failure,
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
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    args = parser.parse_args()

    receipt = deliver(
        _load_json(args.route),
        timeout_seconds=args.timeout_seconds,
        resilience_policy=(
            _load_resilience_policy(args.policy) if args.policy is not None else None
        ),
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
