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


builder = _load(
    "routed_delivery_slo_alert_builder",
    "tools/release/"
    "build_recovery_alert_routed_slo_delivery_routed_delivery_"
    "routed_delivery_slo_alert.py",
)
verifier = _load(
    "routed_delivery_slo_alert_verifier",
    "tools/release/"
    "verify_recovery_alert_delivery_routed_slo_alert_delivery_"
    "routed_delivery_routed_delivery_slo_alerting.py",
)


def _slo(
    status: str = "PASS",
    *,
    authoritative: bool = True,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "overall_status": status,
        "authoritative": authoritative,
    }


def _trend(
    trend: str = "STABLE",
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "overall_trend": trend,
    }


def test_repository_configuration() -> None:
    assert verifier.verify_configuration(ROOT) == ()


def test_pass_does_not_alert() -> None:
    report = builder.build_alert(_slo("PASS"), _trend())
    assert report["alert_state"] == "NONE"
    assert report["should_alert"] is False


def test_warn_creates_advisory_alert() -> None:
    report = builder.build_alert(_slo("WARN"), _trend())
    assert report["alert_state"] == "ADVISORY"
    assert report["severity"] == "warning"


def test_fail_creates_critical_alert() -> None:
    report = builder.build_alert(_slo("FAIL"), _trend())
    assert report["alert_state"] == "CRITICAL"
    assert report["severity"] == "critical"


def test_worsening_trend_can_escalate_advisory() -> None:
    report = builder.build_alert(
        _slo("WARN"),
        _trend("WORSENING"),
    )
    assert report["alert_state"] == "CRITICAL"


def test_insufficient_samples_do_not_alert() -> None:
    report = builder.build_alert(
        _slo(
            "INSUFFICIENT_SAMPLES",
            authoritative=False,
        ),
        _trend("INSUFFICIENT_HISTORY"),
    )
    assert report["alert_state"] == "NON_AUTHORITATIVE"
    assert report["should_alert"] is False


def test_consecutive_non_passing_escalates() -> None:
    report = builder.build_alert(
        _slo("WARN"),
        _trend(),
        consecutive_non_passing=3,
        escalation_threshold=3,
    )
    assert report["alert_state"] == "ESCALATED"


def test_external_delivery_is_disabled() -> None:
    report = builder.build_alert(_slo("FAIL"), _trend())
    assert report["external_delivery_enabled"] is False


def test_summary_contains_alert_state() -> None:
    report = builder.build_alert(_slo("WARN"), _trend())
    summary = builder.render_summary(report)

    assert "Alert state" in summary
    assert "Severity" in summary
    assert "Reason" in summary


def test_report_is_secret_safe() -> None:
    report = builder.build_alert(_slo("FAIL"), _trend())
    assert verifier.verify_report(report) == ()


def test_verifier_rejects_secret_material() -> None:
    report = builder.build_alert(_slo("FAIL"), _trend())
    report["endpoint_url"] = "https://example.invalid"

    assert any("endpoint_url" in error for error in verifier.verify_report(report))
