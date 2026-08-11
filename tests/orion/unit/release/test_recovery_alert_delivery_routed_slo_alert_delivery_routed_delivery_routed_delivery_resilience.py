from __future__ import annotations

import importlib.util
import io
import sys
import urllib.error
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]


def _load(name: str, relative: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError(relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


delivery = _load(
    "routed_delivery_resilient_delivery",
    "tools/release/deliver_routed_recovery_slo_delivery_routed_delivery_alert.py",
)
verifier = _load(
    "routed_delivery_resilient_delivery_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_routed_delivery_resilience.py",
)


def _route(logical_route: str = "operations") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "delivery_id": "source-delivery-id",
        "logical_route": logical_route,
        "route_reason": "advisory_alert",
        "source_alert_severity": "ADVISORY",
        "source_alert_escalated": False,
        "source_alert_authoritative": True,
        "provider_neutral": True,
        "external_delivery_enabled": False,
    }


def _policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "max_attempts": 3,
        "initial_backoff_seconds": 1.0,
        "max_backoff_seconds": 4.0,
        "retry_transport_errors": True,
        "retry_http_statuses": [408, 425, 429, 500, 502, 503, 504],
        "preserve_delivery_id": True,
        "max_attempt_records": 3,
    }


class _Response:
    def __init__(self, status: int = 202) -> None:
        self.status = status

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _env() -> dict[str, str]:
    return {
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_OPERATIONS_URL": "https://example.invalid/operations",
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_OPERATIONS_HMAC_SECRET": "ops-secret",
    }


def test_repository_configuration() -> None:
    assert verifier.verify_configuration(ROOT) == ()


def test_success_on_first_attempt() -> None:
    with (
        patch.dict(delivery.os.environ, _env(), clear=True),
        patch.object(delivery.urllib.request, "urlopen", return_value=_Response(202)),
        patch.object(delivery.time, "sleep"),
    ):
        receipt = delivery.deliver(_route(), resilience_policy=_policy())
    assert receipt["delivery_status"] == "DELIVERED"
    assert receipt["attempt_count"] == 1
    assert receipt["retry_count"] == 0


def test_retryable_http_status_retries_then_succeeds() -> None:
    retry_error = urllib.error.HTTPError(
        "https://example.invalid/operations", 503, "Service Unavailable", {}, io.BytesIO()
    )
    with (
        patch.dict(delivery.os.environ, _env(), clear=True),
        patch.object(
            delivery.urllib.request,
            "urlopen",
            side_effect=[retry_error, _Response(202)],
        ),
        patch.object(delivery.time, "sleep") as sleep,
    ):
        receipt = delivery.deliver(_route(), resilience_policy=_policy())
    assert receipt["delivery_status"] == "DELIVERED"
    assert receipt["attempt_count"] == 2
    assert receipt["retry_count"] == 1
    sleep.assert_called_once_with(1.0)


def test_non_retryable_http_status_stops() -> None:
    error = urllib.error.HTTPError(
        "https://example.invalid/operations", 400, "Bad Request", {}, io.BytesIO()
    )
    with (
        patch.dict(delivery.os.environ, _env(), clear=True),
        patch.object(delivery.urllib.request, "urlopen", side_effect=error) as urlopen,
        patch.object(delivery.time, "sleep"),
    ):
        receipt = delivery.deliver(_route(), resilience_policy=_policy())
    assert urlopen.call_count == 1
    assert receipt["attempt_count"] == 1
    assert receipt["failure_classification"] == "http_error"


def test_transport_error_retries() -> None:
    transport_error = urllib.error.URLError("temporary failure")
    with (
        patch.dict(delivery.os.environ, _env(), clear=True),
        patch.object(
            delivery.urllib.request,
            "urlopen",
            side_effect=[transport_error, _Response(202)],
        ),
        patch.object(delivery.time, "sleep") as sleep,
    ):
        receipt = delivery.deliver(_route(), resilience_policy=_policy())
    assert receipt["delivery_status"] == "DELIVERED"
    assert receipt["retry_count"] == 1
    sleep.assert_called_once_with(1.0)


def test_max_attempts_is_bounded() -> None:
    error = urllib.error.HTTPError(
        "https://example.invalid/operations", 503, "Service Unavailable", {}, io.BytesIO()
    )
    with (
        patch.dict(delivery.os.environ, _env(), clear=True),
        patch.object(delivery.urllib.request, "urlopen", side_effect=error) as urlopen,
        patch.object(delivery.time, "sleep"),
    ):
        receipt = delivery.deliver(_route(), resilience_policy=_policy())
    assert urlopen.call_count == 3
    assert receipt["attempt_count"] == 3
    assert receipt["retry_count"] == 2
    assert len(receipt["attempts"]) == 3


def test_delivery_id_is_preserved_across_attempts() -> None:
    error = urllib.error.HTTPError(
        "https://example.invalid/operations", 503, "Service Unavailable", {}, io.BytesIO()
    )
    with (
        patch.dict(delivery.os.environ, _env(), clear=True),
        patch.object(
            delivery.urllib.request,
            "urlopen",
            side_effect=[error, _Response(202)],
        ),
        patch.object(delivery.time, "sleep"),
    ):
        receipt = delivery.deliver(_route(), resilience_policy=_policy())
    ids = {attempt["delivery_id"] for attempt in receipt["attempts"]}
    assert ids == {receipt["delivery_id"]}


def test_backoff_is_bounded() -> None:
    policy = _policy()
    policy["max_attempts"] = 4
    policy["initial_backoff_seconds"] = 3.0
    policy["max_backoff_seconds"] = 4.0
    policy["max_attempt_records"] = 4
    error = urllib.error.HTTPError(
        "https://example.invalid/operations", 503, "Service Unavailable", {}, io.BytesIO()
    )
    with (
        patch.dict(delivery.os.environ, _env(), clear=True),
        patch.object(delivery.urllib.request, "urlopen", side_effect=error),
        patch.object(delivery.time, "sleep") as sleep,
    ):
        delivery.deliver(_route(), resilience_policy=policy)
    assert [call.args[0] for call in sleep.call_args_list] == [3.0, 4.0, 4.0]


def test_none_route_has_zero_attempts() -> None:
    receipt = delivery.deliver(_route("none"), resilience_policy=_policy())
    assert receipt["delivery_status"] == "NOT_REQUIRED"
    assert receipt["attempt_count"] == 0
    assert receipt["retry_count"] == 0
    assert receipt["attempts"] == []


def test_receipt_is_secret_safe() -> None:
    receipt = delivery.deliver(_route("none"), resilience_policy=_policy())
    assert delivery.verify_secret_safe(receipt) == ()
    assert verifier.verify_receipt(receipt) == ()


def test_receipt_verifier_rejects_secret_material() -> None:
    receipt = delivery.deliver(_route("none"), resilience_policy=_policy())
    receipt["endpoint_url"] = "https://example.invalid"
    assert any("endpoint_url" in error for error in verifier.verify_receipt(receipt))
