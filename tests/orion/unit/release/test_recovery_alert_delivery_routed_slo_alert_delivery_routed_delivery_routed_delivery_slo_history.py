from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[4]


def _load(name: str, relative: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        name,
        ROOT / relative,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(relative)

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


history_builder = _load(
    "routed_delivery_slo_history_builder",
    "tools/release/build_recovery_alert_routed_slo_delivery_routed_delivery_routed_delivery_slo_history.py",
)
trend_analyzer = _load(
    "routed_delivery_slo_trend_analyzer",
    "tools/release/analyze_recovery_alert_routed_slo_delivery_routed_delivery_routed_delivery_slo_trends.py",
)
verifier = _load(
    "routed_delivery_slo_history_verifier",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_routed_delivery_slo_history.py",
)


def _entry(
    *,
    success: float = 1.0,
    retry: float = 0.0,
    attempts: float = 1.0,
    transport: float = 0.0,
    authoritative: bool = True,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "sample_count": 100,
        "minimum_samples": 3,
        "authoritative": authoritative,
        "overall_status": "PASS",
        "metrics": {
            "delivery_success_rate": {
                "value": success,
                "status": "PASS",
            },
            "retry_rate": {
                "value": retry,
                "status": "PASS",
            },
            "average_attempts": {
                "value": attempts,
                "status": "PASS",
            },
            "transport_failure_rate": {
                "value": transport,
                "status": "PASS",
            },
        },
        "provider_neutral": True,
        "external_export_enabled": False,
    }


def test_repository_configuration() -> None:
    assert verifier.verify_configuration(ROOT) == ()


def test_history_is_bounded() -> None:
    history: list[dict[str, Any]] = []

    for index in range(30):
        history = history_builder.build_history(
            history,
            _entry(success=1.0 - (index / 1000)),
            max_entries=20,
        )

    assert len(history) == 20


def test_history_is_deduplicated() -> None:
    observation = _entry()
    history = history_builder.build_history([], observation)
    history = history_builder.build_history(history, observation)

    assert len(history) == 1


def test_history_is_secret_safe() -> None:
    history = history_builder.build_history([], _entry())
    assert verifier.verify_history(history) == ()


def test_trend_requires_minimum_samples() -> None:
    history = history_builder.build_history([], _entry())
    report = trend_analyzer.analyze_trends(history)

    assert report["overall_trend"] == "INSUFFICIENT_HISTORY"


def test_trend_detects_worsening_delivery() -> None:
    observations = [
        _entry(success=1.00, retry=0.01, attempts=1.01),
        _entry(success=0.995, retry=0.02, attempts=1.02),
        _entry(success=0.99, retry=0.03, attempts=1.03),
        _entry(success=0.97, retry=0.10, attempts=1.15),
        _entry(success=0.96, retry=0.15, attempts=1.20),
        _entry(success=0.95, retry=0.20, attempts=1.25),
    ]

    history: list[dict[str, Any]] = []
    for observation in observations:
        history = history_builder.build_history(
            history,
            observation,
        )

    report = trend_analyzer.analyze_trends(history)
    assert report["overall_trend"] == "WORSENING"


def test_trend_detects_improving_delivery() -> None:
    observations = [
        _entry(success=0.95, retry=0.20, attempts=1.25),
        _entry(success=0.96, retry=0.15, attempts=1.20),
        _entry(success=0.97, retry=0.10, attempts=1.15),
        _entry(success=0.99, retry=0.03, attempts=1.03),
        _entry(success=0.995, retry=0.02, attempts=1.02),
        _entry(success=1.00, retry=0.01, attempts=1.01),
    ]

    history: list[dict[str, Any]] = []
    for observation in observations:
        history = history_builder.build_history(
            history,
            observation,
        )

    report = trend_analyzer.analyze_trends(history)
    assert report["overall_trend"] == "IMPROVING"


def test_trend_summary_contains_metrics() -> None:
    observations = [
        _entry(success=0.990),
        _entry(success=0.991),
        _entry(success=0.992),
        _entry(success=0.993),
    ]

    history: list[dict[str, Any]] = []
    for observation in observations:
        history = history_builder.build_history(
            history,
            observation,
        )

    report = trend_analyzer.analyze_trends(history)
    summary = trend_analyzer.render_summary(report)

    assert "delivery_success_rate" in summary
    assert "retry_rate" in summary
    assert "average_attempts" in summary
    assert "transport_failure_rate" in summary


def test_trend_verifier_rejects_secret_material() -> None:
    report = trend_analyzer.analyze_trends(history_builder.build_history([], _entry()))
    report["endpoint_url"] = "https://example.invalid"

    assert any("endpoint_url" in error for error in verifier.verify_trends(report))
