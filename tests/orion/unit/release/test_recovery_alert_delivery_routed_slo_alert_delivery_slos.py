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
    "routed_slo_delivery_slos",
    "tools/release/evaluate_recovery_alert_routed_slo_delivery_slos.py",
)
verify = _load(
    "routed_slo_delivery_slos_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_slos.py",
)


def _policy() -> dict[str, Any]:
    return {
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


def _observation(
    *,
    delivered: bool = True,
    attempt_count: int = 1,
    retry_count: int = 0,
    failure_class: str | None = None,
) -> dict[str, Any]:
    return {
        "delivery_id": "musicclean-routed-slo-123",
        "route": "operations",
        "status": "DELIVERED" if delivered else "FAILED",
        "metrics": {
            "attempted": True,
            "delivered": delivered,
            "attempt_count": attempt_count,
            "retry_count": retry_count,
            "http_status": 202 if delivered else None,
            "failure_class": failure_class,
        },
    }


def test_repository_routed_slo_delivery_slo_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_healthy_observation_passes() -> None:
    report = evaluator.evaluate(_observation(), _policy())
    assert report["status"] == "PASS"


def test_minimum_sample_gate_is_non_authoritative() -> None:
    policy = _policy()
    policy["sample_count"] = 2

    report = evaluator.evaluate(_observation(delivered=False), policy)

    assert report["authoritative"] is False
    assert report["status"] == "INSUFFICIENT_SAMPLES"


def test_delivery_failure_fails_success_rate() -> None:
    report = evaluator.evaluate(_observation(delivered=False), _policy())

    success = next(metric for metric in report["metrics"] if metric["name"] == "success_rate")

    assert success["status"] == "FAIL"
    assert report["status"] == "FAIL"


def test_retry_rate_can_fail() -> None:
    report = evaluator.evaluate(
        _observation(attempt_count=2, retry_count=1),
        _policy(),
    )

    retry = next(metric for metric in report["metrics"] if metric["name"] == "retry_rate")

    assert retry["status"] == "FAIL"


def test_average_attempts_can_warn() -> None:
    policy = _policy()
    policy["average_attempts_warn"] = 1.5
    policy["average_attempts_fail"] = 3.0

    report = evaluator.evaluate(
        _observation(attempt_count=2, retry_count=1),
        policy,
    )

    metric = next(item for item in report["metrics"] if item["name"] == "average_attempts")

    assert metric["status"] == "WARN"


def test_transport_failure_rate_can_fail() -> None:
    report = evaluator.evaluate(
        _observation(
            delivered=False,
            failure_class="TRANSPORT",
        ),
        _policy(),
    )

    metric = next(item for item in report["metrics"] if item["name"] == "transport_failure_rate")

    assert metric["status"] == "FAIL"


def test_summary_contains_all_metrics() -> None:
    report = evaluator.evaluate(_observation(), _policy())
    summary = evaluator.render_summary(report)

    assert "success_rate" in summary
    assert "retry_rate" in summary
    assert "average_attempts" in summary
    assert "transport_failure_rate" in summary


def test_report_verifier_rejects_secret_material() -> None:
    report = evaluator.evaluate(_observation(), _policy())
    report["webhook_url"] = "https://secret.example.test"

    errors = verify.verify_report(report)

    assert any("webhook_url" in error for error in errors)
