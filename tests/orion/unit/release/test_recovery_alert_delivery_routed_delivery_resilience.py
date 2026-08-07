from __future__ import annotations

import importlib.util
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
    "musicclean_routed_delivery_resilience",
    "tools/release/deliver_routed_recovery_alert.py",
)
verify = _load(
    "musicclean_routed_delivery_resilience_verify",
    "tools/release/verify_recovery_alert_delivery_routed_delivery_resilience.py",
)


class _Response:
    def __init__(self, status: int) -> None:
        self.status = status


def _route() -> dict[str, Any]:
    return {
        "route_required": True,
        "route": "operations",
        "severity": "CRITICAL",
        "escalation_required": False,
        "reasons": ["severity route"],
    }


def _alert() -> dict[str, Any]:
    return {
        "alert_required": True,
        "severity": "CRITICAL",
        "reasons": ["delivery SLO failed"],
    }


def _policy() -> dict[str, Any]:
    return {
        "max_attempts": 4,
        "initial_backoff_seconds": 1,
        "backoff_multiplier": 2,
        "max_backoff_seconds": 8,
        "retry_server_errors": True,
        "retry_status_codes": [408, 425, 429],
        "retry_transport_errors": True,
    }


def test_repository_routed_delivery_resilience_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_terminal_400_does_not_retry() -> None:
    calls = 0

    def opener(request: Any, timeout: float) -> _Response:
        nonlocal calls
        calls += 1
        return _Response(400)

    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery",
        "secret",
        retry_policy=_policy(),
        opener=opener,
        sleeper=lambda _: None,
    )

    assert calls == 1
    assert receipt["attempts"] == 1
    assert receipt["failure_class"] == "terminal-http"


def test_429_retries_and_records_attempt_history() -> None:
    statuses = iter([429, 429, 202])
    sleeps: list[float] = []

    def opener(request: Any, timeout: float) -> _Response:
        return _Response(next(statuses))

    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery",
        "secret",
        retry_policy=_policy(),
        opener=opener,
        sleeper=sleeps.append,
    )

    assert receipt["delivered"] is True
    assert receipt["attempts"] == 3
    assert [item["status_code"] for item in receipt["attempt_history"]] == [
        429,
        429,
        202,
    ]
    assert sleeps == [1.0, 2.0]


def test_503_retries_are_bounded() -> None:
    calls = 0

    def opener(request: Any, timeout: float) -> _Response:
        nonlocal calls
        calls += 1
        return _Response(503)

    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery",
        "secret",
        retry_policy=_policy(),
        opener=opener,
        sleeper=lambda _: None,
    )

    assert calls == 4
    assert receipt["attempts"] == 4
    assert receipt["delivered"] is False
    assert receipt["failure_class"] == "retryable-http"


def test_transport_failure_retries() -> None:
    calls = 0

    def opener(request: Any, timeout: float) -> _Response:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise TimeoutError("timeout")
        return _Response(200)

    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery",
        "secret",
        retry_policy=_policy(),
        opener=opener,
        sleeper=lambda _: None,
    )

    assert calls == 3
    assert receipt["delivered"] is True
    assert receipt["attempts"] == 3


def test_delivery_id_is_stable_across_retries() -> None:
    captured_ids: list[str] = []
    statuses = iter([503, 200])

    def opener(request: Any, timeout: float) -> _Response:
        headers = {key.lower(): value for key, value in request.header_items()}
        captured_ids.append(headers["x-musicclean-delivery-id"])
        return _Response(next(statuses))

    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery",
        "secret",
        retry_policy=_policy(),
        opener=opener,
        sleeper=lambda _: None,
    )

    assert len(captured_ids) == 2
    assert len(set(captured_ids)) == 1
    assert receipt["delivery_id"] == captured_ids[0]


def test_route_is_preserved_across_attempt_history() -> None:
    receipt = delivery.deliver(
        _route(),
        _alert(),
        "https://ops.example.test/recovery",
        "secret",
        retry_policy=_policy(),
        opener=lambda request, timeout: _Response(503),
        sleeper=lambda _: None,
    )

    assert receipt["route"] == "operations"
    assert receipt["attempts"] == 4
    assert all(
        item["attempt"] == index for index, item in enumerate(receipt["attempt_history"], start=1)
    )
