from __future__ import annotations

import importlib.util
import io
import os
import sys
import urllib.error
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]


def _load(name: str, relative: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        name,
        ROOT / relative,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(relative)

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


delivery = _load(
    "routed_delivery_sender",
    "tools/release/deliver_routed_recovery_slo_delivery_routed_delivery_routed_delivery_alert.py",
)
verifier = _load(
    "routed_delivery_verifier",
    "tools/release/"
    "verify_recovery_alert_delivery_routed_slo_alert_delivery_"
    "routed_delivery_routed_delivery_routed_delivery.py",
)


def _route(logical_route: str = "operations") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "alert_state": "ADVISORY",
        "severity": "warning",
        "should_alert": logical_route != "none",
        "slo_authoritative": logical_route != "none",
        "logical_route": logical_route,
        "route_reason": "test",
        "provider_neutral": True,
        "external_delivery_enabled": False,
    }


class _Response:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def getcode(self) -> int:
        return self.status


def test_repository_configuration() -> None:
    assert verifier.verify_configuration(ROOT) == ()


def test_none_route_does_not_deliver() -> None:
    receipt = delivery.deliver(_route("none"))
    assert receipt["delivery_attempted"] is False
    assert receipt["failure_classification"] == "not_required"


def test_missing_credentials_are_classified() -> None:
    with patch.dict(os.environ, {}, clear=True):
        receipt = delivery.deliver(_route("operations"))

    assert receipt["delivery_attempted"] is False
    assert receipt["failure_classification"] == "missing_credentials"


def test_plain_http_is_rejected() -> None:
    env = {
        "ORION_ROUTED_SLO_OPERATIONS_WEBHOOK_URL": ("http://example.invalid/hook"),
        "ORION_ROUTED_SLO_OPERATIONS_HMAC_SECRET": "secret",
    }

    with patch.dict(os.environ, env, clear=True):
        receipt = delivery.deliver(_route("operations"))

    assert receipt["delivery_attempted"] is False
    assert receipt["failure_classification"] == "insecure_endpoint"


def test_operations_route_posts_signed_payload() -> None:
    env = {
        "ORION_ROUTED_SLO_OPERATIONS_WEBHOOK_URL": ("https://example.invalid/operations"),
        "ORION_ROUTED_SLO_OPERATIONS_HMAC_SECRET": "secret",
    }

    with (
        patch.dict(os.environ, env, clear=True),
        patch.object(
            delivery.urllib.request,
            "urlopen",
            return_value=_Response(204),
        ) as urlopen,
    ):
        receipt = delivery.deliver(_route("operations"))

    request = urlopen.call_args.args[0]
    headers = {key.lower(): value for key, value in request.header_items()}

    assert receipt["delivered"] is True
    assert headers["x-orion-route"] == "operations"
    assert headers["x-orion-signature"].startswith("sha256=")
    assert headers["x-orion-delivery-id"] == receipt["delivery_id"]


def test_incident_route_posts_signed_payload() -> None:
    env = {
        "ORION_ROUTED_SLO_INCIDENT_WEBHOOK_URL": ("https://example.invalid/incident"),
        "ORION_ROUTED_SLO_INCIDENT_HMAC_SECRET": "secret",
    }

    with (
        patch.dict(os.environ, env, clear=True),
        patch.object(
            delivery.urllib.request,
            "urlopen",
            return_value=_Response(202),
        ),
    ):
        receipt = delivery.deliver(_route("incident_response"))

    assert receipt["delivered"] is True
    assert receipt["http_status"] == 202


def test_delivery_id_is_deterministic() -> None:
    env = {
        "ORION_ROUTED_SLO_OPERATIONS_WEBHOOK_URL": ("https://example.invalid/operations"),
        "ORION_ROUTED_SLO_OPERATIONS_HMAC_SECRET": "secret",
    }

    with (
        patch.dict(os.environ, env, clear=True),
        patch.object(
            delivery.urllib.request,
            "urlopen",
            return_value=_Response(200),
        ),
    ):
        first = delivery.deliver(_route("operations"))
        second = delivery.deliver(_route("operations"))

    assert first["delivery_id"] == second["delivery_id"]


def test_http_error_is_classified() -> None:
    env = {
        "ORION_ROUTED_SLO_OPERATIONS_WEBHOOK_URL": ("https://example.invalid/operations"),
        "ORION_ROUTED_SLO_OPERATIONS_HMAC_SECRET": "secret",
    }

    error = urllib.error.HTTPError(
        "https://example.invalid/operations",
        503,
        "service unavailable",
        {},
        io.BytesIO(),
    )

    with (
        patch.dict(os.environ, env, clear=True),
        patch.object(
            delivery.urllib.request,
            "urlopen",
            side_effect=error,
        ),
    ):
        receipt = delivery.deliver(_route("operations"))

    assert receipt["delivered"] is False
    assert receipt["http_status"] == 503
    assert receipt["failure_classification"] == "http_error"


def test_transport_error_is_classified() -> None:
    env = {
        "ORION_ROUTED_SLO_OPERATIONS_WEBHOOK_URL": ("https://example.invalid/operations"),
        "ORION_ROUTED_SLO_OPERATIONS_HMAC_SECRET": "secret",
    }

    with (
        patch.dict(os.environ, env, clear=True),
        patch.object(
            delivery.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("offline"),
        ),
    ):
        receipt = delivery.deliver(_route("operations"))

    assert receipt["delivered"] is False
    assert receipt["failure_classification"] == "transport_error"


def test_receipt_is_secret_safe() -> None:
    receipt = delivery.deliver(_route("none"))
    assert verifier.verify_receipt(receipt) == ()


def test_receipt_verifier_rejects_secret_material() -> None:
    receipt = delivery.deliver(_route("none"))
    receipt["endpoint_url"] = "https://example.invalid"

    assert any("endpoint_url" in error for error in verifier.verify_receipt(receipt))
