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
        raise RuntimeError(f"unable to load release tool: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


delivery = _load(
    "musicclean_recovery_delivery_resilience",
    "tools/release/deliver_recovery_alert.py",
)
verify = _load(
    "musicclean_recovery_delivery_resilience_verify",
    "tools/release/verify_recovery_alert_delivery_resilience.py",
)


def _policy() -> dict[str, Any]:
    return {
        "request_timeout_seconds": 10,
        "max_attempts": 4,
        "initial_backoff_seconds": 1,
        "maximum_backoff_seconds": 8,
        "retry_statuses": [408, 429],
        "retry_server_errors": True,
        "require_https": True,
        "sign_payload": True,
        "idempotency_header": "X-MusicClean-Delivery-ID",
        "signature_header": "X-MusicClean-Signature-SHA256",
    }


class _Response:
    def __init__(self, code: int) -> None:
        self.code = code

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def getcode(self) -> int:
        return self.code


def test_repository_resilience_configuration() -> None:
    assert verify.verify(ROOT) == ()


def test_terminal_400_does_not_retry() -> None:
    attempts = 0

    def opener(request: Any, timeout: float) -> _Response:
        nonlocal attempts
        attempts += 1
        return _Response(400)

    receipt = delivery.deliver(
        alert={"alert_required": True, "severity": "CRITICAL"},
        policy=_policy(),
        webhook_url="https://alerts.example.test/recovery",
        hmac_secret="secret",
        opener=opener,
        sleeper=lambda _: None,
    )

    assert attempts == 1
    assert receipt["failure_class"] == "terminal-http"
    assert receipt["attempts"] == 1


def test_429_retries_and_records_attempt_history() -> None:
    attempts = 0
    sleeps: list[float] = []

    def opener(request: Any, timeout: float) -> _Response:
        nonlocal attempts
        attempts += 1
        return _Response(429 if attempts < 3 else 204)

    receipt = delivery.deliver(
        alert={"alert_required": True, "severity": "CRITICAL"},
        policy=_policy(),
        webhook_url="https://alerts.example.test/recovery",
        hmac_secret="secret",
        opener=opener,
        sleeper=sleeps.append,
    )

    assert receipt["delivered"] is True
    assert receipt["attempts"] == 3
    assert sleeps == [1.0, 2.0]
    assert len(receipt["attempt_history"]) == 3


def test_delivery_id_is_deterministic() -> None:
    alert = {"alert_required": True, "severity": "CRITICAL", "reasons": ["x"]}
    first = delivery._delivery_id(delivery._canonical_payload(alert))
    second = delivery._delivery_id(delivery._canonical_payload(alert))
    assert first == second
    assert len(first) == 64
