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


builder = _load(
    "musicclean_routed_delivery_slo_history",
    "tools/release/build_recovery_alert_routed_delivery_slo_history.py",
)
analyzer = _load(
    "musicclean_routed_delivery_slo_trends",
    "tools/release/analyze_recovery_alert_routed_delivery_slo_trends.py",
)
verify = _load(
    "musicclean_routed_delivery_slo_history_verify",
    "tools/release/verify_recovery_alert_delivery_routed_delivery_slo_history.py",
)


def _policy() -> dict[str, Any]:
    return {
        "history_limit": 52,
        "short_window": 4,
        "long_window": 12,
        "minimum_trend_samples": 4,
        "trend_tolerance": 0.000001,
    }


def _report(
    generated_at: str,
    success_rate: float,
    retry_rate: float,
    status: str = "PASS",
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "sample_count": 100,
        "minimum_samples": 4,
        "authoritative": True,
        "sample_gate": "READY",
        "status": status,
        "current_route": "operations",
        "current_severity": "CRITICAL",
        "evaluations": [
            {
                "metric": "success_rate",
                "value": success_rate,
                "status": status,
                "direction": "higher-is-better",
            },
            {
                "metric": "retry_rate",
                "value": retry_rate,
                "status": status,
                "direction": "lower-is-better",
            },
        ],
    }


def test_repository_routed_delivery_slo_history_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_history_is_bounded() -> None:
    prior = [
        _report(
            f"2026-08-07T00:{index:02d}:00+00:00",
            0.99,
            0.05,
        )
        for index in range(10)
    ]
    current = _report(
        "2026-08-07T01:00:00+00:00",
        0.99,
        0.05,
    )

    history = builder.build_history(
        current,
        prior,
        {"history_limit": 4},
    )

    assert history["record_count"] == 4
    assert history["history_limit"] == 4


def test_history_is_deduplicated() -> None:
    duplicate = _report(
        "2026-08-07T00:00:00+00:00",
        0.99,
        0.05,
    )
    history = builder.build_history(
        duplicate,
        [duplicate, duplicate],
        {"history_limit": 52},
    )
    assert history["record_count"] == 1


def test_trend_requires_minimum_samples() -> None:
    history = builder.build_history(
        _report("2026-08-07T00:02:00+00:00", 0.99, 0.05),
        [
            _report("2026-08-07T00:00:00+00:00", 0.99, 0.05),
            _report("2026-08-07T00:01:00+00:00", 0.99, 0.05),
        ],
        _policy(),
    )

    trend = analyzer.analyze(history, _policy())

    assert trend["authoritative"] is False
    assert trend["overall_trend"] == "INSUFFICIENT_SAMPLES"


def test_trend_detects_worsening_delivery() -> None:
    history = {
        "records": [
            builder._safe_record(
                _report(
                    "2026-08-07T00:00:00+00:00",
                    0.995,
                    0.02,
                )
            ),
            builder._safe_record(
                _report(
                    "2026-08-07T00:01:00+00:00",
                    0.990,
                    0.03,
                )
            ),
            builder._safe_record(
                _report(
                    "2026-08-07T00:02:00+00:00",
                    0.980,
                    0.08,
                    "WARN",
                )
            ),
            builder._safe_record(
                _report(
                    "2026-08-07T00:03:00+00:00",
                    0.960,
                    0.20,
                    "WARN",
                )
            ),
        ]
    }

    trend = analyzer.analyze(history, _policy())

    assert trend["authoritative"] is True
    assert trend["overall_trend"] == "WORSENING"
    assert any(item["trend"] == "WORSENING" for item in trend["metric_trends"])


def test_trend_detects_improving_delivery() -> None:
    history = {
        "records": [
            builder._safe_record(
                _report(
                    "2026-08-07T00:00:00+00:00",
                    0.950,
                    0.20,
                    "WARN",
                )
            ),
            builder._safe_record(
                _report(
                    "2026-08-07T00:01:00+00:00",
                    0.970,
                    0.12,
                    "WARN",
                )
            ),
            builder._safe_record(
                _report(
                    "2026-08-07T00:02:00+00:00",
                    0.985,
                    0.06,
                )
            ),
            builder._safe_record(
                _report(
                    "2026-08-07T00:03:00+00:00",
                    0.995,
                    0.02,
                )
            ),
        ]
    }

    trend = analyzer.analyze(history, _policy())

    assert trend["overall_trend"] == "IMPROVING"


def test_trend_verifier_rejects_secret_material() -> None:
    trend = analyzer.analyze(
        {
            "records": [
                builder._safe_record(
                    _report(
                        "2026-08-07T00:00:00+00:00",
                        0.99,
                        0.05,
                    )
                )
                for _ in range(4)
            ]
        },
        _policy(),
    )
    trend["webhook_url"] = "https://secret.example.test"

    errors = verify.verify_trend(trend)

    assert any("webhook_url" in error for error in errors)
