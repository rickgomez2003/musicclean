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
    "routed_slo_alert", "tools/release/build_recovery_alert_routed_delivery_slo_alert.py"
)
verify = _load(
    "routed_slo_alert_verify",
    "tools/release/verify_recovery_alert_delivery_routed_delivery_slo_alerting.py",
)


def _policy() -> dict[str, Any]:
    return {
        "alert_on_worsening_trend": True,
        "consecutive_nonpass_escalation": 2,
        "warn_severity": "ADVISORY",
        "fail_severity": "CRITICAL",
        "worsening_severity": "ADVISORY",
        "escalated_severity": "ESCALATED",
        "external_delivery_enabled": False,
    }


def _slo(status="PASS", authoritative=True):
    return {
        "status": status,
        "authoritative": authoritative,
        "current_route": "operations",
        "current_severity": "CRITICAL",
    }


def _trend(overall="STABLE", authoritative=True):
    return {"overall_trend": overall, "authoritative": authoritative}


def _history(statuses):
    return {"records": [{"status": s} for s in statuses]}


def test_repository_routed_delivery_slo_alerting_configuration():
    assert verify.verify_configuration(ROOT) == ()


def test_pass_stable_produces_no_alert():
    alert = builder.build_alert(_slo(), _trend(), _history(["PASS"]), _policy())
    assert alert["alert_required"] is False
    assert alert["severity"] == "NONE"


def test_warn_is_advisory():
    alert = builder.build_alert(_slo("WARN"), _trend(), _history(["PASS", "WARN"]), _policy())
    assert alert["alert_required"] is True
    assert alert["severity"] == "ADVISORY"


def test_fail_is_critical():
    alert = builder.build_alert(_slo("FAIL"), _trend(), _history(["PASS", "FAIL"]), _policy())
    assert alert["alert_required"] is True
    assert alert["severity"] == "CRITICAL"


def test_worsening_trend_is_advisory():
    alert = builder.build_alert(_slo("PASS"), _trend("WORSENING"), _history(["PASS"]), _policy())
    assert alert["alert_required"] is True
    assert alert["severity"] == "ADVISORY"


def test_non_authoritative_worsening_does_not_alert():
    alert = builder.build_alert(
        _slo("PASS"), _trend("WORSENING", False), _history(["PASS"]), _policy()
    )
    assert alert["alert_required"] is False


def test_consecutive_nonpass_escalates():
    alert = builder.build_alert(
        _slo("WARN"), _trend(), _history(["PASS", "WARN", "FAIL"]), _policy()
    )
    assert alert["escalated"] is True
    assert alert["severity"] == "ESCALATED"


def test_external_delivery_remains_disabled():
    alert = builder.build_alert(_slo("FAIL"), _trend(), _history(["FAIL"]), _policy())
    assert alert["external_delivery_enabled"] is False


def test_alert_verifier_rejects_secret_material():
    alert = builder.build_alert(_slo("FAIL"), _trend(), _history(["FAIL"]), _policy())
    alert["webhook_url"] = "https://secret.example.test"
    assert any("webhook_url" in error for error in verify.verify_alert(alert))
