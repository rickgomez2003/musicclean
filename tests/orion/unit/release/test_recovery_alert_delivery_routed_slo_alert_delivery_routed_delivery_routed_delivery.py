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
    "routed_delivery_delivery",
    "tools/release/deliver_routed_recovery_slo_delivery_routed_delivery_alert.py",
)
verifier = _load(
    "routed_delivery_delivery_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_routed_delivery.py",
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


class _Response:
    status = 202

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_repository_configuration() -> None:
    assert verifier.verify_configuration(ROOT) == ()


def test_none_route_does_not_deliver() -> None:
    with patch.object(delivery.urllib.request, "urlopen") as urlopen:
        receipt = delivery.deliver(_route("none"))

    urlopen.assert_not_called()
    assert receipt["delivery_status"] == "NOT_REQUIRED"


def test_missing_credentials_are_classified() -> None:
    with patch.dict(delivery.os.environ, {}, clear=True):
        receipt = delivery.deliver(_route("operations"))

    assert receipt["delivery_status"] == "FAILED"
    assert receipt["failure_classification"] == "missing_credentials"


def test_plain_http_is_rejected() -> None:
    env = {
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_OPERATIONS_URL": "http://example.invalid/hook",
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_OPERATIONS_HMAC_SECRET": "secret",
    }
    with patch.dict(delivery.os.environ, env, clear=True):
        receipt = delivery.deliver(_route("operations"))

    assert receipt["failure_classification"] == "insecure_endpoint"


def test_operations_route_posts_signed_payload() -> None:
    env = {
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_OPERATIONS_URL": "https://example.invalid/operations",
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_OPERATIONS_HMAC_SECRET": "ops-secret",
    }

    with (
        patch.dict(delivery.os.environ, env, clear=True),
        patch.object(
            delivery.urllib.request,
            "urlopen",
            return_value=_Response(),
        ) as urlopen,
    ):
        receipt = delivery.deliver(_route("operations"))

    request = urlopen.call_args.args[0]
    assert request.headers["X-orion-signature-sha256"]
    assert request.headers["X-orion-delivery-id"] == receipt["delivery_id"]
    assert receipt["delivery_status"] == "DELIVERED"


def test_incident_route_posts_signed_payload() -> None:
    env = {
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_INCIDENT_URL": "https://example.invalid/incidents",
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_INCIDENT_HMAC_SECRET": "incident-secret",
    }

    with (
        patch.dict(delivery.os.environ, env, clear=True),
        patch.object(
            delivery.urllib.request,
            "urlopen",
            return_value=_Response(),
        ) as urlopen,
    ):
        receipt = delivery.deliver(_route("incident-response"))

    assert urlopen.called
    assert receipt["delivery_status"] == "DELIVERED"


def test_delivery_id_is_deterministic() -> None:
    first = delivery._delivery_id(delivery._canonical_payload(_route()))
    second = delivery._delivery_id(delivery._canonical_payload(_route()))
    assert first == second


def test_http_error_is_classified() -> None:
    env = {
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_OPERATIONS_URL": "https://example.invalid/operations",
        "ORION_ROUTED_SLO_ROUTED_DELIVERY_OPERATIONS_HMAC_SECRET": "ops-secret",
    }
    error = urllib.error.HTTPError(
        "https://example.invalid/operations",
        503,
        "Service Unavailable",
        {},
        io.BytesIO(),
    )

    with (
        patch.dict(delivery.os.environ, env, clear=True),
        patch.object(delivery.urllib.request, "urlopen", side_effect=error),
    ):
        receipt = delivery.deliver(_route("operations"))

    assert receipt["http_status"] == 503
    assert receipt["failure_classification"] == "http_error"


def test_receipt_is_secret_safe() -> None:
    receipt = delivery.deliver(_route("none"))
    assert delivery.verify_secret_safe(receipt) == ()
    assert verifier.verify_receipt(receipt) == ()


def test_receipt_verifier_rejects_secret_material() -> None:
    receipt = delivery.deliver(_route("none"))
    receipt["hmac_secret"] = "secret"
    assert any("hmac_secret" in error for error in verifier.verify_receipt(receipt))
