from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

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


history_tool = _load(
    "musicclean_delivery_slo_history",
    "tools/release/build_recovery_alert_delivery_slo_history.py",
)
trend_tool = _load(
    "musicclean_delivery_slo_trend",
    "tools/release/analyze_recovery_alert_delivery_slo_trends.py",
)
verify = _load(
    "musicclean_delivery_slo_history_verify",
    "tools/release/verify_recovery_alert_delivery_slo_history.py",
)


def _report(ts: str, status: str, success: float, retry: float, latency: float):
    return {
        "generated_at": ts,
        "status": status,
        "objectives": {
            "success_rate": {"value": success, "status": status},
            "retry_rate": {"value": retry, "status": status},
            "terminal_failure_rate": {"value": 0.0, "status": "PASS"},
            "average_latency_seconds": {"value": latency, "status": status},
        },
    }


def test_repository_delivery_slo_history_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_history_is_bounded_and_deduplicated(tmp_path: Path) -> None:
    prior = tmp_path / "prior"
    prior.mkdir()
    for index in range(5):
        folder = prior / str(index)
        folder.mkdir()
        report = _report(
            f"2026-08-0{index + 1}T00:00:00+00:00",
            "PASS",
            1.0,
            0.0,
            1.0,
        )
        (folder / "recovery-alert-delivery-slo.json").write_text(
            json.dumps(report),
            encoding="utf-8",
        )

    current = _report("2026-08-06T00:00:00+00:00", "WARN", 0.98, 0.15, 6.0)
    history = history_tool.build_history(prior, current, 4)
    assert len(history) == 4
    assert history[-1]["status"] == "WARN"


def test_trend_requires_minimum_samples() -> None:
    report = trend_tool.analyze(
        {"records": [_report("2026-08-01", "PASS", 1.0, 0.0, 1.0)]},
        4,
        12,
        4,
    )
    assert report["trend_status"] == "INSUFFICIENT_DATA"


def test_trend_detects_worsening_delivery() -> None:
    records = [
        _report("2026-08-01", "PASS", 1.00, 0.00, 1.0),
        _report("2026-08-02", "PASS", 1.00, 0.00, 1.0),
        _report("2026-08-03", "PASS", 0.99, 0.02, 1.5),
        _report("2026-08-04", "WARN", 0.98, 0.15, 6.0),
        _report("2026-08-05", "WARN", 0.97, 0.18, 7.0),
        _report("2026-08-06", "FAIL", 0.90, 0.40, 12.0),
    ]
    report = trend_tool.analyze({"records": records}, 3, 6, 4)
    assert report["trend_status"] == "worsening"
    assert report["consecutive_warn_fail"] == 3
