from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime, timedelta
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


evaluate = _load(
    "musicclean_recovery_slo_eval",
    "tools/release/evaluate_recovery_slos.py",
)
verify = _load(
    "musicclean_recovery_slo_verify",
    "tools/release/verify_recovery_slos.py",
)


def _policy() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status_levels": ["PASS", "WARN", "FAIL"],
        "duration_seconds": {"warning": 720, "objective": 900},
        "successful_drill_age_days": {"warning": 10, "objective": 14},
        "success_ratio": {
            "warning": 0.98,
            "objective": 0.95,
            "minimum_samples": 4,
        },
    }


def _drill(
    *,
    now: datetime,
    elapsed: float = 300.0,
    days_old: float = 1.0,
    status: str = "PASS",
) -> dict[str, object]:
    completed = now - timedelta(days=days_old)
    return {
        "drill_id": "owner/repo:123",
        "tag": "v0.6.44",
        "status": status,
        "elapsed_seconds": elapsed,
        "completed_at": completed.isoformat(),
    }


def test_repository_recovery_slo_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_recovery_slo_passes_when_all_objectives_are_healthy() -> None:
    now = datetime(2026, 8, 5, tzinfo=UTC)
    latest = _drill(now=now, elapsed=300, days_old=1)
    history = [_drill(now=now, days_old=float(i)) for i in range(4)]

    report = evaluate.evaluate(
        policy=_policy(),
        latest_drill=latest,
        history=history,
        now=now,
    )

    assert report["status"] == "PASS"


def test_recovery_slo_warns_before_duration_objective_is_breached() -> None:
    now = datetime(2026, 8, 5, tzinfo=UTC)
    latest = _drill(now=now, elapsed=800, days_old=1)
    history = [_drill(now=now, days_old=float(i)) for i in range(4)]

    report = evaluate.evaluate(
        policy=_policy(),
        latest_drill=latest,
        history=history,
        now=now,
    )

    assert report["status"] == "WARN"
    assert report["metrics"]["recovery_duration_seconds"]["status"] == "WARN"


def test_recovery_slo_fails_when_duration_objective_is_breached() -> None:
    now = datetime(2026, 8, 5, tzinfo=UTC)
    latest = _drill(now=now, elapsed=901, days_old=1)
    history = [_drill(now=now, days_old=float(i)) for i in range(4)]

    report = evaluate.evaluate(
        policy=_policy(),
        latest_drill=latest,
        history=history,
        now=now,
    )

    assert report["status"] == "FAIL"


def test_recovery_slo_warns_with_insufficient_history() -> None:
    now = datetime(2026, 8, 5, tzinfo=UTC)
    latest = _drill(now=now, elapsed=300, days_old=1)

    report = evaluate.evaluate(
        policy=_policy(),
        latest_drill=latest,
        history=[latest],
        now=now,
    )

    assert report["status"] == "WARN"
    assert report["reason"] == "insufficient drill history"
