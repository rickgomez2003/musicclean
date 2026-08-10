from __future__ import annotations

import hashlib
import hmac
import importlib.util
import sys
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
    "routed_slo_delivery_delivery",
    "tools/release/deliver_routed_recovery_slo_delivery_alert.py",
)
verify = _load(
    "routed_slo_delivery_delivery_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery.py",
)


def _route(name: str = "operations") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "delivery_id": "upstream-route-id",
        "source_route": "operations",
        "severity": "ADVISORY",
        "route": name,
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


def test_repository_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_none_route_does_not_deliver() -> None:
    receipt = delivery.deliver(
        _route("none"),
        _alert(),
        endpoint_url=None,
        hmac_secret=None,
    )
    assert receipt["delivered"] is False
    assert receipt["failure_classification"] == "route_none"


def test_missing_credentials_are_classified() -> None:
    receipt = delivery.deliver(
        _route("operations"),
        _alert(),
        endpoint_url=None,
        hmac_secret=None,
    )
    assert receipt["delivered"] is False
    assert receipt["failure_classification"] == "credentials_unavailable"


def test_plain_http_is_rejected() -> None:
    try:
        delivery.deliver(
            _route(),
            _alert(),
            endpoint_url="http://example.invalid/hook",
            hmac_secret="secret",
        )
    except ValueError as exc:
        assert "HTTPS" in str(exc)
    else:
        raise AssertionError("plain HTTP was accepted")


def test_operations_route_posts_signed_payload() -> None:
    observed: dict[str, Any] = {}

    def transport(request: Any, timeout: float) -> int:
        observed["timeout"] = timeout
        observed["url"] = request.full_url
        observed["body"] = request.data
        observed["headers"] = dict(request.header_items())
        return 204

    receipt = delivery.deliver(
        _route("operations"),
        _alert(),
        endpoint_url="https://example.test/hook",
        hmac_secret="secret",
        transport=transport,
    )

    assert receipt["delivered"] is True
    assert receipt["http_status"] == 204
    assert observed["url"] == "https://example.test/hook"

    body = observed["body"]
    expected = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    assert observed["headers"]["X-musicclean-signature"] == f"sha256={expected}"


def test_incident_route_posts_signed_payload() -> None:
    called = False

    def transport(request: Any, timeout: float) -> int:
        nonlocal called
        called = True
        return 200

    receipt = delivery.deliver(
        _route("incident-response"),
        _alert(),
        endpoint_url="https://example.test/incident",
        hmac_secret="secret",
        transport=transport,
    )
    assert called is True
    assert receipt["delivered"] is True


def test_delivery_id_is_deterministic() -> None:
    first = delivery.deliver(
        _route("none"),
        _alert(),
        endpoint_url=None,
        hmac_secret=None,
    )
    second = delivery.deliver(
        _route("none"),
        _alert(),
        endpoint_url=None,
        hmac_secret=None,
    )
    assert first["delivery_id"] == second["delivery_id"]


def test_receipt_is_secret_safe() -> None:
    receipt = delivery.deliver(
        _route("none"),
        _alert(),
        endpoint_url=None,
        hmac_secret=None,
    )
    assert delivery.verify_receipt_secret_safe(receipt) == ()


def test_receipt_verifier_rejects_secret_material() -> None:
    receipt = delivery.deliver(
        _route("none"),
        _alert(),
        endpoint_url=None,
        hmac_secret=None,
    )
    receipt["hmac_secret"] = "secret"
    assert any("hmac_secret" in e for e in verify.verify_receipt(receipt))
