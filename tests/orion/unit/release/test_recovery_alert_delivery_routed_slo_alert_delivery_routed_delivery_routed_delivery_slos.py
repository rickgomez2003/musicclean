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


evaluator = _load(
    "routed_delivery_slo_evaluator",
    "tools/release/evaluate_recovery_alert_routed_slo_delivery_routed_delivery_routed_delivery_slos.py",
)
verifier = _load(
    "routed_delivery_slo_verifier",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_routed_delivery_slos.py",
)


def _policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "minimum_samples": 3,
        "delivery_success_rate_pass": 0.99,
        "delivery_success_rate_warn": 0.97,
        "retry_rate_pass": 0.10,
        "retry_rate_warn": 0.25,
        "average_attempts_pass": 1.10,
        "average_attempts_warn": 1.50,
        "transport_failure_rate_pass": 0.01,
        "transport_failure_rate_warn": 0.05,
        "external_export_enabled": False,
        "provider_neutral": True,
    }


def _observability(
    *,
    samples: int = 100,
    successes: int = 100,
    retries: int = 0,
    attempts: int = 100,
    transport_failures: int = 0,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "sample_count": samples,
        "success_count": successes,
        "retry_count_total": retries,
        "attempt_count_total": attempts,
        "transport_failure_count": transport_failures,
        "delivery_status": "DELIVERED",
        "attempt_count": 1,
        "retry_count": 0,
        "transport_failure": False,
    }


def test_repository_configuration() -> None:
    assert verifier.verify_configuration(ROOT) == ()


def test_healthy_observation_passes() -> None:
    report = evaluator.evaluate(_observability(), _policy())
    assert report["overall_status"] == "PASS"
    assert report["authoritative"] is True


def test_minimum_sample_gate_is_non_authoritative() -> None:
    report = evaluator.evaluate(
        _observability(samples=2, successes=2, attempts=2),
        _policy(),
    )
    assert report["overall_status"] == "INSUFFICIENT_SAMPLES"
    assert report["authoritative"] is False


def test_delivery_failure_fails_success_rate() -> None:
    report = evaluator.evaluate(
        _observability(samples=100, successes=90, attempts=100),
        _policy(),
    )
    assert report["metrics"]["delivery_success_rate"]["status"] == "FAIL"
    assert report["overall_status"] == "FAIL"


def test_retry_rate_can_fail() -> None:
    report = evaluator.evaluate(
        _observability(retries=30, attempts=130),
        _policy(),
    )
    assert report["metrics"]["retry_rate"]["status"] == "FAIL"


def test_average_attempts_can_warn() -> None:
    report = evaluator.evaluate(
        _observability(retries=15, attempts=120),
        _policy(),
    )
    assert report["metrics"]["average_attempts"]["status"] == "WARN"


def test_transport_failure_rate_can_fail() -> None:
    report = evaluator.evaluate(
        _observability(transport_failures=10),
        _policy(),
    )
    assert report["metrics"]["transport_failure_rate"]["status"] == "FAIL"


def test_summary_contains_all_metrics() -> None:
    report = evaluator.evaluate(_observability(), _policy())
    summary = evaluator.render_summary(report)

    assert "delivery_success_rate" in summary
    assert "retry_rate" in summary
    assert "average_attempts" in summary
    assert "transport_failure_rate" in summary


def test_report_is_secret_safe() -> None:
    report = evaluator.evaluate(_observability(), _policy())
    assert verifier.verify_report(report) == ()


def test_report_verifier_rejects_secret_material() -> None:
    report = evaluator.evaluate(_observability(), _policy())
    report["endpoint_url"] = "https://example.invalid"
    assert any("endpoint_url" in error for error in verifier.verify_report(report))
