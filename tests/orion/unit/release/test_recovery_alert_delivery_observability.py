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


observe = _load(
    "musicclean_recovery_delivery_observability",
    "tools/release/build_recovery_delivery_observability.py",
)
verify = _load(
    "musicclean_recovery_delivery_observability_verify",
    "tools/release/verify_recovery_alert_delivery_observability.py",
)


def _policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "history_limit": 52,
    }


def test_repository_observability_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_observation_records_attempts_retries_and_success_rate() -> None:
    receipt = {
        "delivery_id": "abc",
        "delivery_required": True,
        "delivered": True,
        "attempts": 3,
        "status_code": 204,
        "failure_class": None,
        "provider": "generic-webhook",
        "elapsed_seconds": 1.25,
    }
    history = [
        {
            "delivery_required": True,
            "delivered": True,
            "attempts": 1,
            "failure_class": None,
        },
        {
            "delivery_required": True,
            "delivered": False,
            "attempts": 4,
            "failure_class": "terminal-http",
        },
    ]

    observation = observe.build(
        receipt=receipt,
        history=history,
        policy=_policy(),
    )

    assert observation["attempt_count"] == 3
    assert observation["retry_count"] == 2
    assert observation["sample_count"] == 3
    assert observation["success_rate"] == 2 / 3
    assert observation["aggregate_attempt_count"] == 8
    assert observation["aggregate_retry_count"] == 5
    assert observation["retry_rate"] == 5 / 8
    assert observation["terminal_failure_count"] == 1
    assert observation["terminal_failure_rate"] == 1 / 3
    assert observation["average_latency_seconds"] == 1.25
    assert observation["maximum_latency_seconds"] == 1.25


def test_summary_contains_no_destination_or_secret_material() -> None:
    observation = {
        "delivery_id": "abc",
        "delivered": False,
        "attempt_count": 4,
        "retry_count": 3,
        "status_code": 503,
        "failure_class": "transient-http",
        "sample_count": 5,
        "success_rate": 0.8,
    }

    summary = observe.render_summary(observation)

    assert "https://" not in summary
    assert "RECOVERY_ALERT_WEBHOOK" not in summary
    assert "secret" not in summary.lower()
