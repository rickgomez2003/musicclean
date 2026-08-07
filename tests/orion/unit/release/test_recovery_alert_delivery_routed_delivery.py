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
    "musicclean_routed_delivery",
    "tools/release/deliver_routed_recovery_alert.py",
)
verify = _load(
    "musicclean_routed_delivery_verify",
    "tools/release/verify_recovery_alert_delivery_routed_delivery.py",
)


class _Response:
    def __init__(self, status: int) -> None:
        self.status = status


def _alert() -> dict[str, Any]:
    return {
        "alert_required": True,
        "severity": "CRITICAL",
        "reasons": ["delivery SLO failed"],
    }


def _route(route: str = "operations") -> dict[str, Any]:
    return {
        "route_required": True,
        "route": route,
        "severity": "CRITICAL",
        "escalation_required": route == "incident-response",
        "reasons": ["severity route"],
    }


def test_repository_routed_delivery_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_no_route_required_produces_no_delivery() -> None:
    receipt = delivery.deliver(
        {
            "route_required": False,
            "route": "none",
            "severity": "NONE",
        },
        {"alert_required": False, "severity": "NONE"},
        "https://alerts.example.test/recovery",
        "secret",
    )
    assert receipt["delivered"] is False
    assert receipt["route_required"] is False


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
        "https://ops.example.test/recovery",
        "secret",
        opener=opener,
    )

    assert receipt["delivered"] is True
    assert receipt["route"] == "operations"
    assert captured["url"] == "https://ops.example.test/recovery"
    assert captured["body"]["route"] == "operations"
    headers = {key.lower(): value for key, value in captured["headers"].items()}
    assert "x-musicclean-signature-sha256" in headers
    assert headers["x-musicclean-signature-sha256"].startswith("sha256=")
    assert len(headers["x-musicclean-signature-sha256"]) == len("sha256=") + 64


def test_incident_route_uses_incident_endpoint() -> None:
    captured: dict[str, Any] = {}

    def opener(request: Any, timeout: float) -> _Response:
        captured["url"] = request.full_url
        return _Response(200)

    receipt = delivery.deliver(
        _route("incident-response"),
        _alert(),
        "https://incident.example.test/recovery",
        "secret",
        opener=opener,
    )

    assert receipt["delivered"] is True
    assert captured["url"] == "https://incident.example.test/recovery"


def test_plain_http_is_rejected() -> None:
    try:
        delivery.deliver(
            _route(),
            _alert(),
            "http://alerts.example.test/recovery",
            "secret",
        )
    except ValueError as exc:
        assert "HTTPS" in str(exc)
    else:
        raise AssertionError("plain HTTP endpoint was accepted")


def test_terminal_http_failure_is_recorded() -> None:
    def opener(request: Any, timeout: float) -> _Response:
        return _Response(400)

    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery",
        "secret",
        opener=opener,
    )

    assert receipt["delivered"] is False
    assert receipt["status_code"] == 400
    assert receipt["failure_class"] == "terminal-http"


def test_retryable_http_failure_is_classified() -> None:
    def opener(request: Any, timeout: float) -> _Response:
        return _Response(503)

    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery",
        "secret",
        opener=opener,
    )

    assert receipt["delivered"] is False
    assert receipt["failure_class"] == "retryable-http"
