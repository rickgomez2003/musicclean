from __future__ import annotations

import importlib.util
import sys
import urllib.error
from pathlib import Path
from types import ModuleType
from typing import Any

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
    "routed_slo_delivery_resilience",
    "tools/release/deliver_routed_recovery_slo_delivery_alert.py",
)
verify = _load(
    "routed_slo_delivery_resilience_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_resilience.py",
)


def _route() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "delivery_id": "upstream-route-id",
        "source_route": "operations",
        "severity": "ADVISORY",
        "route": "operations",
        "external_delivery_enabled": False,
        "provider_neutral": True,
    }


def _alert() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "delivery_id": "upstream-alert-id",
        "route": "operations",
        "severity": "ADVISORY",
    }


def _policy() -> dict[str, Any]:
    return {
        "max_attempts": 3,
        "base_delay_seconds": 1.0,
        "max_delay_seconds": 4.0,
        "retryable_http_statuses": [408, 425, 429, 500, 502, 503, 504],
        "retry_transport_errors": True,
        "preserve_delivery_id": True,
    }


def test_repository_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_success_on_first_attempt() -> None:
    receipt = delivery.deliver(
        _route(),
        _alert(),
        endpoint_url="https://example.test/hook",
        hmac_secret="secret",
        resilience=_policy(),
        transport=lambda request, timeout: 204,
        sleeper=lambda delay: None,
    )
    assert receipt["delivered"] is True
    assert receipt["attempt_count"] == 1
    assert receipt["retry_count"] == 0


def test_retryable_http_status_retries_then_succeeds() -> None:
    statuses = iter([503, 204])
    delays: list[float] = []

    receipt = delivery.deliver(
        _route(),
        _alert(),
        endpoint_url="https://example.test/hook",
        hmac_secret="secret",
        resilience=_policy(),
        transport=lambda request, timeout: next(statuses),
        sleeper=delays.append,
    )

    assert receipt["delivered"] is True
    assert receipt["attempt_count"] == 2
    assert receipt["retry_count"] == 1
    assert delays == [1.0]


def test_non_retryable_http_status_stops() -> None:
    receipt = delivery.deliver(
        _route(),
        _alert(),
        endpoint_url="https://example.test/hook",
        hmac_secret="secret",
        resilience=_policy(),
        transport=lambda request, timeout: 400,
        sleeper=lambda delay: None,
    )

    assert receipt["delivered"] is False
    assert receipt["attempt_count"] == 1
    assert receipt["retry_count"] == 0


def test_transport_error_retries() -> None:
    calls = 0

    def transport(request: Any, timeout: float) -> int:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise urllib.error.URLError("temporary")
        return 200

    receipt = delivery.deliver(
        _route(),
        _alert(),
        endpoint_url="https://example.test/hook",
        hmac_secret="secret",
        resilience=_policy(),
        transport=transport,
        sleeper=lambda delay: None,
    )

    assert receipt["delivered"] is True
    assert receipt["attempt_count"] == 3
    assert receipt["retry_count"] == 2


def test_max_attempts_is_bounded() -> None:
    receipt = delivery.deliver(
        _route(),
        _alert(),
        endpoint_url="https://example.test/hook",
        hmac_secret="secret",
        resilience=_policy(),
        transport=lambda request, timeout: 503,
        sleeper=lambda delay: None,
    )

    assert receipt["delivered"] is False
    assert receipt["attempt_count"] == 3
    assert receipt["retry_count"] == 2


def test_delivery_id_is_preserved_across_attempts() -> None:
    seen: list[str] = []
    statuses = iter([503, 204])

    def transport(request: Any, timeout: float) -> int:
        seen.append(request.get_header("X-MusicClean-Delivery-ID"))
        return next(statuses)

    delivery.deliver(
        _route(),
        _alert(),
        endpoint_url="https://example.test/hook",
        hmac_secret="secret",
        resilience=_policy(),
        transport=transport,
        sleeper=lambda delay: None,
    )

    assert len(seen) == 2
    assert seen[0] == seen[1]


def test_backoff_is_bounded() -> None:
    delays: list[float] = []
    policy = _policy()
    policy["max_attempts"] = 4
    policy["base_delay_seconds"] = 2.0
    policy["max_delay_seconds"] = 3.0

    delivery.deliver(
        _route(),
        _alert(),
        endpoint_url="https://example.test/hook",
        hmac_secret="secret",
        resilience=policy,
        transport=lambda request, timeout: 503,
        sleeper=delays.append,
    )

    assert delays == [2.0, 3.0, 3.0]


def test_receipt_is_secret_safe() -> None:
    receipt = delivery.deliver(
        _route(),
        _alert(),
        endpoint_url="https://example.test/hook",
        hmac_secret="secret",
        resilience=_policy(),
        transport=lambda request, timeout: 204,
        sleeper=lambda delay: None,
    )

    assert delivery.verify_receipt_secret_safe(receipt) == ()
    assert verify.verify_receipt(receipt) == ()


def test_receipt_verifier_rejects_secret_material() -> None:
    receipt = delivery.deliver(
        _route(),
        _alert(),
        endpoint_url="https://example.test/hook",
        hmac_secret="secret",
        resilience=_policy(),
        transport=lambda request, timeout: 204,
        sleeper=lambda delay: None,
    )
    receipt["hmac_secret"] = "secret"

    assert any("hmac_secret" in e for e in verify.verify_receipt(receipt))
