from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[4]


def _load(name: str, relative: str) -> ModuleType:
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


delivery = _load(
    "musicclean_routed_slo_alert_delivery",
    "tools/release/deliver_routed_recovery_slo_alert.py",
)
verify = _load(
    "musicclean_routed_slo_alert_delivery_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery.py",
)


class _Response:
    def __init__(self, status: int) -> None:
        self.status = status

    def getcode(self) -> int:
        return self.status


def _route(
    route: str = "operations",
    required: bool = True,
) -> dict[str, Any]:
    return {
        "route": route,
        "route_required": required,
        "severity": "ADVISORY",
        "escalated": False,
        "source_route": "operations",
    }


def _alert() -> dict[str, Any]:
    return {
        "alert_required": True,
        "severity": "ADVISORY",
        "escalated": False,
        "reasons": ["test"],
        "current_status": "WARN",
        "trend": "STABLE",
        "consecutive_nonpass_count": 1,
    }


def test_repository_routed_slo_alert_delivery_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_none_route_does_not_deliver() -> None:
    receipt = delivery.deliver(
        _route("none", False),
        _alert(),
        "https://unused.example.test",
        "unused",
    )
    assert receipt["attempted"] is False
    assert receipt["status"] == "NOT_REQUIRED"


def test_operations_route_posts_signed_payload() -> None:
    captured: dict[str, Any] = {}

    def opener(request: Any, timeout: float) -> _Response:
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response(202)

    receipt = delivery.deliver(
        _route("operations"),
        _alert(),
        "https://ops.example.test/recovery-slo",
        "secret",
        opener=opener,
    )

    assert receipt["delivered"] is True
    assert receipt["route"] == "operations"
    assert captured["url"] == "https://ops.example.test/recovery-slo"
    assert captured["body"]["route"] == "operations"

    headers = {key.lower(): value for key, value in captured["headers"].items()}
    signature = headers["x-musicclean-signature-sha256"]
    assert signature.startswith("sha256=")
    assert len(signature) == len("sha256=") + 64


def test_plain_http_is_rejected() -> None:
    try:
        delivery.deliver(
            _route("operations"),
            _alert(),
            "http://ops.example.test/recovery-slo",
            "secret",
        )
    except ValueError as exc:
        assert "HTTPS" in str(exc)
    else:
        raise AssertionError("plain HTTP should be rejected")


def test_delivery_id_is_deterministic() -> None:
    def opener(request: Any, timeout: float) -> _Response:
        return _Response(202)

    first = delivery.deliver(
        _route("operations"),
        _alert(),
        "https://ops.example.test/recovery-slo",
        "secret",
        opener=opener,
    )
    second = delivery.deliver(
        _route("operations"),
        _alert(),
        "https://ops.example.test/recovery-slo",
        "secret",
        opener=opener,
    )
    assert first["delivery_id"] == second["delivery_id"]


def test_receipt_verifier_rejects_secret_material() -> None:
    receipt = {
        "schema_version": 1,
        "route": "operations",
        "status": "DELIVERED",
        "webhook_url": "https://secret.example.test",
    }
    errors = verify.verify_receipt(receipt)
    assert any("webhook_url" in error for error in errors)
