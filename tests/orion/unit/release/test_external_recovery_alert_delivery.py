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
    "musicclean_external_recovery_alert_delivery",
    "tools/release/deliver_recovery_alert.py",
)
verify = _load(
    "musicclean_external_recovery_alert_delivery_verify",
    "tools/release/verify_external_recovery_alert_delivery.py",
)


def _policy() -> dict[str, Any]:
    return {
        "environment": "recovery-alert-delivery",
        "url_secret": "RECOVERY_ALERT_WEBHOOK_URL",
        "hmac_secret": "RECOVERY_ALERT_WEBHOOK_HMAC_SECRET",
        "connect_timeout_seconds": 5,
        "request_timeout_seconds": 10,
        "max_attempts": 3,
        "require_https": True,
        "sign_payload": True,
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


def test_repository_external_delivery_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_healthy_alert_is_not_delivered() -> None:
    receipt = delivery.deliver(
        alert={"alert_required": False, "severity": None},
        policy=_policy(),
        webhook_url="",
        hmac_secret="",
    )
    assert receipt["delivery_required"] is False
    assert receipt["attempts"] == 0


def test_alert_delivery_posts_signed_payload() -> None:
    requests: list[Any] = []

    def opener(request: Any, timeout: float) -> _Response:
        requests.append((request, timeout))
        return _Response(204)

    receipt = delivery.deliver(
        alert={"alert_required": True, "severity": "CRITICAL"},
        policy=_policy(),
        webhook_url="https://alerts.example.test/recovery",
        hmac_secret="secret",
        opener=opener,
        sleeper=lambda _: None,
    )

    assert receipt["delivered"] is True
    assert receipt["attempts"] == 1
    request, timeout = requests[0]
    assert timeout == 10.0
    assert request.get_header("X-musicclean-signature-sha256") is not None


def test_external_delivery_rejects_plain_http() -> None:
    try:
        delivery.deliver(
            alert={"alert_required": True, "severity": "CRITICAL"},
            policy=_policy(),
            webhook_url="http://alerts.example.test/recovery",
            hmac_secret="secret",
        )
    except ValueError as exc:
        assert "must use HTTPS" in str(exc)
    else:
        raise AssertionError("expected HTTPS enforcement failure")


def test_failed_delivery_retries_bounded_number_of_times() -> None:
    attempts = 0

    def opener(request: Any, timeout: float) -> _Response:
        nonlocal attempts
        attempts += 1
        return _Response(503)

    receipt = delivery.deliver(
        alert={"alert_required": True, "severity": "ESCALATED"},
        policy=_policy(),
        webhook_url="https://alerts.example.test/recovery",
        hmac_secret="secret",
        opener=opener,
        sleeper=lambda _: None,
    )

    assert receipt["delivered"] is False
    assert receipt["attempts"] == 3
    assert attempts == 3
