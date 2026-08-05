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
    "musicclean_recovery_history",
    "tools/release/build_recovery_history.py",
)
trend_tool = _load(
    "musicclean_recovery_trends",
    "tools/release/analyze_recovery_trends.py",
)
verify = _load(
    "musicclean_recovery_history_verify",
    "tools/release/verify_recovery_slo_history.py",
)


def _record(drill_id: str, completed_at: str, status: str, elapsed: float) -> dict[str, object]:
    return {
        "drill_id": drill_id,
        "completed_at": completed_at,
        "status": status,
        "elapsed_seconds": elapsed,
    }


def test_repository_history_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_history_deduplicates_orders_and_bounds(tmp_path: Path) -> None:
    prior = tmp_path / "prior"
    prior.mkdir()

    first = prior / "a"
    first.mkdir()
    (first / "recovery-drill.json").write_text(
        json.dumps(_record("one", "2026-08-01T00:00:00+00:00", "PASS", 300)),
        encoding="utf-8",
    )

    duplicate = prior / "b"
    duplicate.mkdir()
    (duplicate / "recovery-drill.json").write_text(
        json.dumps(_record("one", "2026-08-02T00:00:00+00:00", "PASS", 290)),
        encoding="utf-8",
    )

    current = tmp_path / "current.json"
    current.write_text(
        json.dumps(_record("two", "2026-08-03T00:00:00+00:00", "PASS", 280)),
        encoding="utf-8",
    )

    result = history_tool.build_history(
        prior_root=prior,
        current_record=current,
        maximum_records=2,
    )

    assert [item["drill_id"] for item in result] == ["one", "two"]
    assert result[0]["completed_at"] == "2026-08-02T00:00:00+00:00"


def test_trend_reports_insufficient_data_with_too_few_samples() -> None:
    records = [_record("one", "2026-08-01T00:00:00+00:00", "PASS", 300)]
    result = trend_tool.analyze(
        records,
        short_window=4,
        long_window=12,
        minimum_trend_samples=4,
    )
    assert result["duration_trend"] == "INSUFFICIENT_DATA"


def test_trend_detects_improving_duration() -> None:
    records = [
        _record("1", "2026-08-01T00:00:00+00:00", "PASS", 500),
        _record("2", "2026-08-02T00:00:00+00:00", "PASS", 480),
        _record("3", "2026-08-03T00:00:00+00:00", "PASS", 300),
        _record("4", "2026-08-04T00:00:00+00:00", "PASS", 290),
    ]
    result = trend_tool.analyze(
        records,
        short_window=4,
        long_window=12,
        minimum_trend_samples=4,
    )
    assert result["duration_trend"] == "IMPROVING"
    assert result["short_window"]["success_ratio"] == 1.0
