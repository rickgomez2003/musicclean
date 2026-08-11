from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[4]


def _load(name: str, relative: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError(relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


evaluate = _load(
    "routed_delivery_slos",
    "tools/release/evaluate_recovery_alert_routed_slo_delivery_routed_delivery_slos.py",
)
verify = _load(
    "routed_delivery_slos_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_slos.py",
)


def _policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "minimum_samples": 5,
        "sample_count": 5,
        "success_rate_warn": 0.99,
        "success_rate_fail": 0.95,
        "retry_rate_warn": 0.10,
        "retry_rate_fail": 0.25,
        "average_attempts_warn": 1.25,
        "average_attempts_fail": 2.0,
        "transport_failure_rate_warn": 0.02,
        "transport_failure_rate_fail": 0.05,
    }


def _observation() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "delivery_id": "delivery-1",
        "logical_route": "operations",
        "delivered": True,
        "attempt_count": 1,
        "retry_count": 0,
        "terminal_http_status": 204,
        "failure_classification": None,
    }


def test_repository_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_healthy_observation_passes() -> None:
    report = evaluate.evaluate(_observation(), _policy())
    assert report["authoritative"] is True
    assert report["overall_classification"] == "PASS"


def test_minimum_sample_gate_is_non_authoritative() -> None:
    policy = _policy()
    policy["sample_count"] = 2
    report = evaluate.evaluate(_observation(), policy)
    assert report["authoritative"] is False
    assert report["overall_classification"] == "INSUFFICIENT_SAMPLES"


def test_delivery_failure_fails_success_rate() -> None:
    observation = _observation()
    observation["delivered"] = False
    report = evaluate.evaluate(observation, _policy())
    assert report["metrics"]["success_rate"]["classification"] == "FAIL"


def test_retry_rate_can_fail() -> None:
    observation = _observation()
    observation["retry_count"] = 1
    report = evaluate.evaluate(observation, _policy())
    assert report["metrics"]["retry_rate"]["classification"] == "FAIL"


def test_average_attempts_can_warn() -> None:
    observation = _observation()
    observation["attempt_count"] = 1.5
    report = evaluate.evaluate(observation, _policy())
    assert report["metrics"]["average_attempts"]["classification"] == "WARN"


def test_transport_failure_rate_can_fail() -> None:
    observation = _observation()
    observation["failure_classification"] = "transport_error"
    report = evaluate.evaluate(observation, _policy())
    assert report["metrics"]["transport_failure_rate"]["classification"] == "FAIL"


def test_summary_contains_all_metrics() -> None:
    report = evaluate.evaluate(_observation(), _policy())
    summary = evaluate.render_summary(report)
    assert "success_rate" in summary
    assert "retry_rate" in summary
    assert "average_attempts" in summary
    assert "transport_failure_rate" in summary


def test_report_verifier_rejects_secret_material() -> None:
    report = evaluate.evaluate(_observation(), _policy())
    report["hmac_secret"] = "secret"
    assert any("hmac_secret" in error for error in verify.verify_report(report))
