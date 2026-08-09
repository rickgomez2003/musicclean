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
    "routed_slo_alerting", "tools/release/build_recovery_alert_routed_slo_delivery_slo_alert.py"
)
verify = _load(
    "routed_slo_alerting_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_slo_alerting.py",
)


def _policy() -> dict[str, Any]:
    return {
        "warn_severity": "ADVISORY",
        "fail_severity": "CRITICAL",
        "worsening_trend_severity": "ADVISORY",
        "alert_on_worsening_trend": True,
        "escalate_after_consecutive_non_passing": 3,
        "external_delivery_enabled": False,
        "provider_neutral": True,
    }


def _slo(status: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "delivery_id": "musicclean-routed-slo-123",
        "route": "operations",
        "authoritative": True,
        "status": status,
        "metrics": [],
    }


def test_repository_configuration():
    assert verify.verify_configuration(ROOT) == ()


def test_pass_none():
    assert builder.build_alert(_slo("PASS"), None, None, _policy())["severity"] == "NONE"


def test_warn_advisory():
    assert builder.build_alert(_slo("WARN"), None, None, _policy())["severity"] == "ADVISORY"


def test_fail_critical():
    assert builder.build_alert(_slo("FAIL"), None, None, _policy())["severity"] == "CRITICAL"


def test_authoritative_worsening_advisory():
    trend = {"authoritative": True, "trend": "WORSENING"}
    assert builder.build_alert(_slo("PASS"), trend, None, _policy())["severity"] == "ADVISORY"


def test_non_authoritative_worsening_suppressed():
    trend = {"authoritative": False, "trend": "WORSENING"}
    assert builder.build_alert(_slo("PASS"), trend, None, _policy())["severity"] == "NONE"


def test_consecutive_non_passing_escalates():
    history = {
        "records": [
            {"status": "PASS", "authoritative": True},
            {"status": "WARN", "authoritative": True},
            {"status": "WARN", "authoritative": True},
            {"status": "FAIL", "authoritative": True},
        ]
    }
    alert = builder.build_alert(_slo("FAIL"), None, history, _policy())
    assert alert["severity"] == "ESCALATED"
    assert alert["consecutive_non_passing"] == 3


def test_external_delivery_disabled():
    assert (
        builder.build_alert(_slo("WARN"), None, None, _policy())["external_delivery_enabled"]
        is False
    )


def test_secret_material_rejected():
    alert = builder.build_alert(_slo("WARN"), None, None, _policy())
    alert["endpoint_url"] = "https://secret.example.test"
    assert any("endpoint_url" in e for e in verify.verify_alert(alert))
