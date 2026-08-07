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


evaluator = _load(
    "musicclean_routed_delivery_slos",
    "tools/release/evaluate_recovery_alert_routed_delivery_slos.py",
)
verify = _load(
    "musicclean_routed_delivery_slos_verify",
    "tools/release/verify_recovery_alert_delivery_routed_delivery_slos.py",
)


def _policy() -> dict[str, Any]:
    return {
        "minimum_samples": 4,
        "success_rate": {
            "warn_below": 0.98,
            "fail_below": 0.95,
        },
        "retry_rate": {
            "warn_above": 0.20,
            "fail_above": 0.35,
        },
        "average_attempts": {
            "warn_above": 1.50,
            "fail_above": 2.00,
        },
        "average_latency_seconds": {
            "warn_above": 5.0,
            "fail_above": 10.0,
        },
        "terminal_http_failure_rate": {
            "warn_above": 0.02,
            "fail_above": 0.05,
        },
        "transport_failure_rate": {
            "warn_above": 0.02,
            "fail_above": 0.05,
        },
    }


def _observation(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "sample_count": 100,
        "success_rate": 0.995,
        "retry_rate": 0.05,
        "average_attempts": 1.05,
        "average_latency_seconds": 1.25,
        "terminal_http_failure_count": 0,
        "transport_failure_count": 0,
        "current_route": "operations",
        "current_severity": "CRITICAL",
    }
    base.update(overrides)
    return base


def test_repository_routed_delivery_slo_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_healthy_observation_passes() -> None:
    report = evaluator.evaluate(_observation(), _policy())
    assert report["authoritative"] is True
    assert report["sample_gate"] == "READY"
    assert report["status"] == "PASS"


def test_minimum_sample_gate_is_non_authoritative() -> None:
    report = evaluator.evaluate(
        _observation(sample_count=3),
        _policy(),
    )
    assert report["authoritative"] is False
    assert report["sample_gate"] == "INSUFFICIENT_SAMPLES"


def test_success_rate_can_warn() -> None:
    report = evaluator.evaluate(
        _observation(success_rate=0.97),
        _policy(),
    )
    assert report["status"] == "WARN"


def test_success_rate_can_fail() -> None:
    report = evaluator.evaluate(
        _observation(success_rate=0.90),
        _policy(),
    )
    assert report["status"] == "FAIL"


def test_retry_rate_can_fail() -> None:
    report = evaluator.evaluate(
        _observation(retry_rate=0.50),
        _policy(),
    )
    assert report["status"] == "FAIL"


def test_average_attempts_can_warn() -> None:
    report = evaluator.evaluate(
        _observation(average_attempts=1.75),
        _policy(),
    )
    assert report["status"] == "WARN"


def test_average_latency_can_fail() -> None:
    report = evaluator.evaluate(
        _observation(average_latency_seconds=12.0),
        _policy(),
    )
    assert report["status"] == "FAIL"


def test_terminal_failure_rate_is_derived_from_counts() -> None:
    report = evaluator.evaluate(
        _observation(
            sample_count=100,
            terminal_http_failure_count=3,
        ),
        _policy(),
    )
    metric = next(
        item for item in report["evaluations"] if item["metric"] == "terminal_http_failure_rate"
    )
    assert metric["value"] == 0.03
    assert metric["status"] == "WARN"


def test_transport_failure_rate_can_fail() -> None:
    report = evaluator.evaluate(
        _observation(
            sample_count=100,
            transport_failure_count=8,
        ),
        _policy(),
    )
    assert report["status"] == "FAIL"


def test_summary_contains_all_metrics() -> None:
    report = evaluator.evaluate(_observation(), _policy())
    summary = evaluator.render_summary(report)
    assert "Routed Recovery Alert Delivery SLOs" in summary
    assert "success_rate" in summary
    assert "transport_failure_rate" in summary


def test_report_verifier_rejects_secret_material() -> None:
    report = evaluator.evaluate(_observation(), _policy())
    report["webhook_url"] = "https://secret.example.test"
    errors = verify.verify_report(report)
    assert any("webhook_url" in error for error in errors)
