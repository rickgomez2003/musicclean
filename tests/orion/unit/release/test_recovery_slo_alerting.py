from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime
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


alert_tool = _load(
    "musicclean_recovery_alert",
    "tools/release/build_recovery_alert.py",
)
verify = _load(
    "musicclean_recovery_alert_verify",
    "tools/release/verify_recovery_slo_alerting.py",
)


def _policy() -> dict[str, object]:
    return {
        "schema_version": 1,
        "suppression_window_hours": 24,
        "consecutive_failure_escalation": 2,
        "provider": "github-summary",
        "external_delivery_enabled": False,
        "severity": {
            "warn": "ADVISORY",
            "fail": "CRITICAL",
            "worsening": "ADVISORY",
            "escalated": "ESCALATED",
        },
    }


def _trend(value: str = "STABLE") -> dict[str, object]:
    return {"duration_trend": value}


def _history(*statuses: str) -> list[dict[str, object]]:
    return [
        {
            "drill_id": f"owner/repo:{index}",
            "status": status,
        }
        for index, status in enumerate(statuses, start=1)
    ]


def test_repository_alert_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_pass_and_stable_produces_no_alert() -> None:
    alert = alert_tool.build_alert(
        policy=_policy(),
        slo_report={"status": "PASS"},
        trend_report=_trend("STABLE"),
        history=_history("PASS"),
        now=datetime(2026, 8, 5, tzinfo=UTC),
    )
    assert alert["alert_required"] is False
    assert alert["severity"] is None


def test_warn_produces_advisory_alert() -> None:
    alert = alert_tool.build_alert(
        policy=_policy(),
        slo_report={"status": "WARN"},
        trend_report=_trend(),
        history=_history("PASS"),
        now=datetime(2026, 8, 5, tzinfo=UTC),
    )
    assert alert["alert_required"] is True
    assert alert["severity"] == "ADVISORY"


def test_fail_produces_critical_alert() -> None:
    alert = alert_tool.build_alert(
        policy=_policy(),
        slo_report={"status": "FAIL"},
        trend_report=_trend(),
        history=_history("PASS", "FAIL"),
        now=datetime(2026, 8, 5, tzinfo=UTC),
    )
    assert alert["severity"] == "CRITICAL"
    assert alert["escalated"] is False


def test_worsening_pass_produces_advisory_alert() -> None:
    alert = alert_tool.build_alert(
        policy=_policy(),
        slo_report={"status": "PASS"},
        trend_report=_trend("WORSENING"),
        history=_history("PASS"),
        now=datetime(2026, 8, 5, tzinfo=UTC),
    )
    assert alert["severity"] == "ADVISORY"


def test_two_consecutive_failures_escalate() -> None:
    alert = alert_tool.build_alert(
        policy=_policy(),
        slo_report={"status": "FAIL"},
        trend_report=_trend(),
        history=_history("PASS", "FAIL", "FAIL"),
        now=datetime(2026, 8, 5, tzinfo=UTC),
    )
    assert alert["severity"] == "ESCALATED"
    assert alert["escalated"] is True
    assert alert["consecutive_failures"] == 2
