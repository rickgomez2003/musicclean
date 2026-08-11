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


builder = _load(
    "routed_delivery_slo_alert",
    "tools/release/build_recovery_alert_routed_slo_delivery_routed_delivery_slo_alert.py",
)
verifier = _load(
    "routed_delivery_slo_alert_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_slo_alerting.py",
)


def _policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "alert_on_warn": True,
        "alert_on_fail": True,
        "alert_on_worsening_trend": True,
        "escalate_after_consecutive_non_passing": 3,
        "external_delivery_enabled": False,
        "provider_neutral": True,
    }


def _slo(classification: str = "PASS", authoritative: bool = True) -> dict[str, Any]:
    return {
        "delivery_id": "delivery-1",
        "logical_route": "operations",
        "overall_classification": classification,
        "authoritative": authoritative,
    }


def _trend(value: str = "STABLE", authoritative: bool = True) -> dict[str, Any]:
    return {
        "overall_trend": value,
        "authoritative": authoritative,
    }


def _history(classes: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "delivery_id": f"delivery-{index}",
            "authoritative": True,
            "overall_classification": classification,
        }
        for index, classification in enumerate(classes, 1)
    ]


def test_repository_configuration() -> None:
    assert verifier.verify_configuration(ROOT) == ()


def test_pass_does_not_alert() -> None:
    alert = builder.build_alert(_slo(), _trend(), [], _policy())
    assert alert["alert"] is False
    assert alert["severity"] == "NONE"


def test_warn_creates_advisory_alert() -> None:
    alert = builder.build_alert(_slo("WARN"), _trend(), [], _policy())
    assert alert["alert"] is True
    assert alert["severity"] == "ADVISORY"


def test_fail_creates_critical_alert() -> None:
    alert = builder.build_alert(_slo("FAIL"), _trend(), [], _policy())
    assert alert["alert"] is True
    assert alert["severity"] == "CRITICAL"


def test_worsening_trend_can_alert() -> None:
    alert = builder.build_alert(
        _slo("PASS"),
        _trend("WORSENING"),
        [],
        _policy(),
    )
    assert alert["alert"] is True
    assert alert["severity"] == "ADVISORY"
    assert "worsening_trend" in alert["reasons"]


def test_insufficient_samples_do_not_alert() -> None:
    alert = builder.build_alert(
        _slo("INSUFFICIENT_SAMPLES", authoritative=False),
        _trend("INSUFFICIENT_SAMPLES", authoritative=False),
        [],
        _policy(),
    )
    assert alert["alert"] is False
    assert alert["severity"] == "NONE"
    assert alert["reasons"] == ["insufficient_samples"]


def test_consecutive_non_passing_escalates() -> None:
    history = _history(["PASS", "WARN", "WARN", "FAIL"])
    alert = builder.build_alert(
        _slo("WARN"),
        _trend(),
        history,
        _policy(),
    )
    assert alert["escalated"] is True
    assert alert["severity"] == "CRITICAL"


def test_external_delivery_is_disabled() -> None:
    alert = builder.build_alert(_slo("WARN"), _trend(), [], _policy())
    assert alert["external_delivery_enabled"] is False
    assert alert["provider_neutral"] is True


def test_summary_contains_alert_state() -> None:
    alert = builder.build_alert(_slo("WARN"), _trend(), [], _policy())
    summary = builder.render_summary(alert)
    assert "Severity: `ADVISORY`" in summary
    assert "Authoritative: `True`" in summary


def test_verifier_rejects_secret_material() -> None:
    alert = builder.build_alert(_slo("WARN"), _trend(), [], _policy())
    alert["hmac_secret"] = "secret"
    assert any("hmac_secret" in error for error in verifier.verify_alert(alert))
