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


evaluate = _load(
    "musicclean_recovery_delivery_slos", "tools/release/evaluate_recovery_alert_delivery_slos.py"
)
verify = _load(
    "musicclean_recovery_delivery_slos_verify",
    "tools/release/verify_recovery_alert_delivery_slos.py",
)


def _policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "minimum_samples": 4,
        "success_rate": {"warn_below": 0.99, "fail_below": 0.95},
        "retry_rate": {"warn_above": 0.10, "fail_above": 0.25},
        "terminal_failure_rate": {"warn_above": 0.02, "fail_above": 0.05},
        "average_latency_seconds": {"warn_above": 5.0, "fail_above": 10.0},
    }


def test_repository_delivery_slo_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_insufficient_samples_are_not_failed() -> None:
    r = evaluate.evaluate(
        {
            "required_sample_count": 3,
            "success_rate": 1.0,
            "retry_rate": 0.0,
            "terminal_failure_rate": 0.0,
            "average_latency_seconds": 1.0,
        },
        _policy(),
    )
    assert r["status"] == "INSUFFICIENT_DATA"


def test_healthy_delivery_slos_pass() -> None:
    r = evaluate.evaluate(
        {
            "required_sample_count": 20,
            "success_rate": 1.0,
            "retry_rate": 0.0,
            "terminal_failure_rate": 0.0,
            "average_latency_seconds": 2.0,
        },
        _policy(),
    )
    assert r["status"] == "PASS"


def test_degraded_delivery_slos_warn() -> None:
    r = evaluate.evaluate(
        {
            "required_sample_count": 20,
            "success_rate": 0.98,
            "retry_rate": 0.15,
            "terminal_failure_rate": 0.03,
            "average_latency_seconds": 6.0,
        },
        _policy(),
    )
    assert r["status"] == "WARN"


def test_bad_delivery_slos_fail() -> None:
    r = evaluate.evaluate(
        {
            "required_sample_count": 20,
            "success_rate": 0.90,
            "retry_rate": 0.40,
            "terminal_failure_rate": 0.10,
            "average_latency_seconds": 12.0,
        },
        _policy(),
    )
    assert r["status"] == "FAIL"
