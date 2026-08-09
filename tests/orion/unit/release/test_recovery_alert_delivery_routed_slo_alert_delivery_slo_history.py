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
    "routed_slo_delivery_slo_history",
    "tools/release/build_recovery_alert_routed_slo_delivery_slo_history.py",
)
trend_analyzer = _load(
    "routed_slo_delivery_slo_trends",
    "tools/release/analyze_recovery_alert_routed_slo_delivery_slo_trends.py",
)
verify = _load(
    "routed_slo_delivery_slo_history_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_slo_history.py",
)


def _policy() -> dict[str, Any]:
    return {
        "max_records": 52,
        "minimum_trend_samples": 4,
        "short_window": 2,
        "long_window": 4,
        "read_only": True,
    }


def _report(
    status: str,
    *,
    delivery_id: str,
    authoritative: bool = True,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "delivery_id": delivery_id,
        "route": "operations",
        "authoritative": authoritative,
        "sample_count": 5,
        "minimum_samples": 5,
        "status": status,
        "metrics": [
            {
                "name": "success_rate",
                "value": 1.0 if status == "PASS" else 0.0,
                "status": status,
            }
        ],
    }


def test_repository_routed_slo_delivery_slo_history_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_history_is_bounded() -> None:
    history: dict[str, Any] | None = None

    for index in range(60):
        history = history_builder.build_history(
            _report("PASS", delivery_id=f"id-{index}"),
            history,
            _policy(),
        )

    assert history is not None
    assert history["record_count"] == 52
    assert len(history["records"]) == 52


def test_history_is_deduplicated() -> None:
    report = _report("PASS", delivery_id="same")

    first = history_builder.build_history(
        report,
        None,
        _policy(),
    )
    second = history_builder.build_history(
        report,
        first,
        _policy(),
    )

    assert second["record_count"] == 1


def test_trend_requires_minimum_samples() -> None:
    history = {
        "records": [
            _report("PASS", delivery_id="1"),
            _report("WARN", delivery_id="2"),
        ]
    }

    trend = trend_analyzer.analyze(history, _policy())

    assert trend["authoritative"] is False
    assert trend["trend"] == "INSUFFICIENT_SAMPLES"


def test_trend_detects_worsening_delivery() -> None:
    history = {
        "records": [
            _report("PASS", delivery_id="1"),
            _report("PASS", delivery_id="2"),
            _report("WARN", delivery_id="3"),
            _report("FAIL", delivery_id="4"),
        ]
    }

    trend = trend_analyzer.analyze(history, _policy())

    assert trend["authoritative"] is True
    assert trend["trend"] == "WORSENING"


def test_trend_detects_improving_delivery() -> None:
    history = {
        "records": [
            _report("FAIL", delivery_id="1"),
            _report("WARN", delivery_id="2"),
            _report("PASS", delivery_id="3"),
            _report("PASS", delivery_id="4"),
        ]
    }

    trend = trend_analyzer.analyze(history, _policy())

    assert trend["trend"] == "IMPROVING"


def test_trend_verifier_rejects_secret_material() -> None:
    data = {
        "schema_version": 1,
        "trend": "STABLE",
        "hmac_secret": "secret",
    }

    errors = verify.verify_evidence(data)

    assert any("hmac_secret" in error for error in errors)
