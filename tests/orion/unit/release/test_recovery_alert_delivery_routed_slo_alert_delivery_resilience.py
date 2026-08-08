from __future__ import annotations

import importlib.util
import sys
import urllib.error
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


delivery = _load("routed_slo_resilience", "tools/release/deliver_routed_recovery_slo_alert.py")
verify = _load(
    "routed_slo_resilience_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_resilience.py",
)


class _Response:
    def __init__(self, status: int) -> None:
        self.status = status

    def getcode(self) -> int:
        return self.status


def _route():
    return {
        "route": "operations",
        "route_required": True,
        "severity": "ADVISORY",
        "escalated": False,
        "source_route": "operations",
    }


def _alert():
    return {
        "alert_required": True,
        "severity": "ADVISORY",
        "escalated": False,
        "reasons": ["test"],
        "current_status": "WARN",
        "trend": "STABLE",
        "consecutive_nonpass_count": 1,
    }


def _policy():
    return {
        "max_attempts": 3,
        "base_delay_seconds": 0.0,
        "max_delay_seconds": 0.0,
        "retryable_http_statuses": [408, 425, 429, 500, 502, 503, 504],
        "retry_transport_errors": True,
    }


def test_repository_routed_slo_alert_delivery_resilience_configuration():
    assert verify.verify_configuration(ROOT) == ()


def test_terminal_400_does_not_retry():
    calls = 0

    def opener(request: Any, timeout: float):
        nonlocal calls
        calls += 1
        raise urllib.error.HTTPError(request.full_url, 400, "Bad Request", {}, None)

    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery-slo",
        "secret",
        retry_policy=_policy(),
        opener=opener,
        sleeper=lambda _: None,
    )
    assert calls == 1
    assert receipt["failure_class"] == "TERMINAL_HTTP"


def test_429_retries_and_records_attempt_history():
    calls = 0

    def opener(request: Any, timeout: float):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise urllib.error.HTTPError(request.full_url, 429, "Too Many Requests", {}, None)
        return _Response(202)

    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery-slo",
        "secret",
        retry_policy=_policy(),
        opener=opener,
        sleeper=lambda _: None,
    )
    assert receipt["delivered"] is True
    assert receipt["attempt_count"] == 2
    assert receipt["attempt_history"][0]["failure_class"] == "RETRYABLE_HTTP"


def test_503_retries_are_bounded():
    calls = 0

    def opener(request: Any, timeout: float):
        nonlocal calls
        calls += 1
        raise urllib.error.HTTPError(request.full_url, 503, "Service Unavailable", {}, None)

    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery-slo",
        "secret",
        retry_policy=_policy(),
        opener=opener,
        sleeper=lambda _: None,
    )
    assert calls == 3
    assert receipt["attempt_count"] == 3


def test_transport_failure_retries():
    calls = 0

    def opener(request: Any, timeout: float):
        nonlocal calls
        calls += 1
        if calls < 3:
            raise urllib.error.URLError("network unavailable")
        return _Response(202)

    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery-slo",
        "secret",
        retry_policy=_policy(),
        opener=opener,
        sleeper=lambda _: None,
    )
    assert receipt["delivered"] is True
    assert receipt["attempt_count"] == 3


def test_delivery_id_is_stable_across_retries():
    ids, calls = [], 0

    def opener(request: Any, timeout: float):
        nonlocal calls
        calls += 1
        headers = {k.lower(): v for k, v in request.header_items()}
        ids.append(headers["x-musicclean-delivery-id"])
        if calls == 1:
            raise urllib.error.HTTPError(request.full_url, 503, "Service Unavailable", {}, None)
        return _Response(202)

    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery-slo",
        "secret",
        retry_policy=_policy(),
        opener=opener,
        sleeper=lambda _: None,
    )
    assert len(set(ids)) == 1
    assert receipt["delivery_id"] == ids[0]


def test_route_is_preserved_across_attempt_history():
    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery-slo",
        "secret",
        retry_policy=_policy(),
        opener=lambda r, timeout: _Response(202),
        sleeper=lambda _: None,
    )
    assert receipt["route"] == "operations"
    assert receipt["attempt_history"][0]["attempt"] == 1
