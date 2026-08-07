from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[4]


def load(name: str, rel: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    if spec is None or spec.loader is None:
        raise RuntimeError(rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = load("delivery_slo_alert", "tools/release/build_recovery_alert_delivery_slo_alert.py")
verify = load(
    "delivery_slo_alert_verify", "tools/release/verify_recovery_alert_delivery_slo_alerting.py"
)


def policy() -> dict[str, object]:
    return {
        "schema_version": 1,
        "minimum_trend_samples": 4,
        "alert_on_worsening_trend": True,
        "consecutive_nonpass_escalation": 2,
        "warn_severity": "ADVISORY",
        "fail_severity": "CRITICAL",
        "worsening_severity": "ADVISORY",
        "escalated_severity": "ESCALATED",
        "external_delivery_enabled": False,
    }


def test_repository_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_pass_stable_no_alert() -> None:
    alert = builder.build_alert(
        {"status": "PASS"},
        {"trend_status": "stable", "sample_count": 12, "consecutive_warn_fail": 0},
        policy(),
    )
    assert alert["alert_required"] is False
    assert alert["severity"] == "NONE"


def test_warn_is_advisory() -> None:
    alert = builder.build_alert(
        {"status": "WARN"},
        {"trend_status": "stable", "sample_count": 12, "consecutive_warn_fail": 1},
        policy(),
    )
    assert alert["severity"] == "ADVISORY"


def test_fail_is_critical() -> None:
    alert = builder.build_alert(
        {"status": "FAIL"},
        {"trend_status": "stable", "sample_count": 12, "consecutive_warn_fail": 1},
        policy(),
    )
    assert alert["severity"] == "CRITICAL"


def test_worsening_is_sample_gated() -> None:
    alert = builder.build_alert(
        {"status": "PASS"},
        {"trend_status": "worsening", "sample_count": 3, "consecutive_warn_fail": 0},
        policy(),
    )
    assert alert["alert_required"] is False
    assert alert["trend_authoritative"] is False


def test_authoritative_worsening_is_advisory() -> None:
    alert = builder.build_alert(
        {"status": "PASS"},
        {"trend_status": "worsening", "sample_count": 12, "consecutive_warn_fail": 0},
        policy(),
    )
    assert alert["severity"] == "ADVISORY"


def test_consecutive_nonpass_escalates() -> None:
    alert = builder.build_alert(
        {"status": "WARN"},
        {"trend_status": "worsening", "sample_count": 12, "consecutive_warn_fail": 2},
        policy(),
    )
    assert alert["severity"] == "ESCALATED"
