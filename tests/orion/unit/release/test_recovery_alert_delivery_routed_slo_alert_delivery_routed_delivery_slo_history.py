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


history_builder = _load(
    "routed_delivery_slo_history",
    "tools/release/build_recovery_alert_routed_slo_delivery_routed_delivery_slo_history.py",
)
trend_analyzer = _load(
    "routed_delivery_slo_trends",
    "tools/release/analyze_recovery_alert_routed_slo_delivery_routed_delivery_slo_trends.py",
)
verifier = _load(
    "routed_delivery_slo_history_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_slo_history.py",
)


def _history_policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "max_records": 30,
        "trend_minimum_samples": 3,
        "trend_tolerance": 0.0,
        "external_export_enabled": False,
    }


def _slo(
    delivery_id: str,
    *,
    success_rate: float = 1.0,
    retry_rate: float = 0.0,
    average_attempts: float = 1.0,
    transport_failure_rate: float = 0.0,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "delivery_id": delivery_id,
        "logical_route": "operations",
        "sample_count": 5,
        "minimum_samples": 5,
        "authoritative": True,
        "overall_classification": "PASS",
        "metrics": {
            "success_rate": {
                "value": success_rate,
                "classification": "PASS",
            },
            "retry_rate": {
                "value": retry_rate,
                "classification": "PASS",
            },
            "average_attempts": {
                "value": average_attempts,
                "classification": "PASS",
            },
            "transport_failure_rate": {
                "value": transport_failure_rate,
                "classification": "PASS",
            },
        },
    }


def test_repository_configuration() -> None:
    assert verifier.verify_configuration(ROOT) == ()


def test_history_is_bounded() -> None:
    policy = _history_policy()
    policy["max_records"] = 3

    history: list[dict[str, Any]] = []
    for index in range(5):
        history = history_builder.build_history(
            _slo(f"delivery-{index}"),
            history,
            policy,
        )

    assert len(history) == 3
    assert [item["delivery_id"] for item in history] == [
        "delivery-2",
        "delivery-3",
        "delivery-4",
    ]


def test_history_is_deduplicated() -> None:
    history = history_builder.build_history(
        _slo("delivery-1"),
        [],
        _history_policy(),
    )
    replacement = _slo("delivery-1", retry_rate=1.0)
    history = history_builder.build_history(
        replacement,
        history,
        _history_policy(),
    )

    assert len(history) == 1
    assert history[0]["metrics"]["retry_rate"]["value"] == 1.0


def test_history_is_secret_safe() -> None:
    history = history_builder.build_history(
        _slo("delivery-1"),
        [],
        _history_policy(),
    )
    assert history_builder.verify_secret_safe(history) == ()
    assert verifier.verify_history(history) == ()


def test_trend_requires_minimum_samples() -> None:
    history = [
        history_builder._entry(_slo("delivery-1")),
        history_builder._entry(_slo("delivery-2")),
    ]
    report = trend_analyzer.analyze(history, _history_policy())

    assert report["authoritative"] is False
    assert report["overall_trend"] == "INSUFFICIENT_SAMPLES"


def test_trend_detects_worsening_delivery() -> None:
    history = [
        history_builder._entry(_slo("delivery-1", retry_rate=0.0)),
        history_builder._entry(_slo("delivery-2", retry_rate=0.1)),
        history_builder._entry(_slo("delivery-3", retry_rate=0.3)),
    ]
    report = trend_analyzer.analyze(history, _history_policy())

    assert report["authoritative"] is True
    assert report["metrics"]["retry_rate"]["trend"] == "WORSENING"
    assert report["overall_trend"] == "WORSENING"


def test_trend_detects_improving_delivery() -> None:
    history = [
        history_builder._entry(_slo("delivery-1", success_rate=0.90)),
        history_builder._entry(_slo("delivery-2", success_rate=0.95)),
        history_builder._entry(_slo("delivery-3", success_rate=1.00)),
    ]
    report = trend_analyzer.analyze(history, _history_policy())

    assert report["metrics"]["success_rate"]["trend"] == "IMPROVING"
    assert report["overall_trend"] == "IMPROVING"


def test_trend_summary_contains_metrics() -> None:
    history = [
        history_builder._entry(_slo("delivery-1")),
        history_builder._entry(_slo("delivery-2")),
        history_builder._entry(_slo("delivery-3")),
    ]
    report = trend_analyzer.analyze(history, _history_policy())
    summary = trend_analyzer.render_summary(report)

    assert "success_rate" in summary
    assert "retry_rate" in summary
    assert "average_attempts" in summary
    assert "transport_failure_rate" in summary


def test_trend_verifier_rejects_secret_material() -> None:
    history = [
        history_builder._entry(_slo("delivery-1")),
        history_builder._entry(_slo("delivery-2")),
        history_builder._entry(_slo("delivery-3")),
    ]
    report = trend_analyzer.analyze(history, _history_policy())
    report["hmac_secret"] = "secret"

    assert any("hmac_secret" in error for error in verifier.verify_trend(report))
