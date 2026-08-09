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
    "routed_slo_routing", "tools/release/build_recovery_alert_routed_slo_delivery_slo_route.py"
)
verify = _load(
    "routed_slo_routing_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_slo_routing.py",
)


def _policy() -> dict[str, Any]:
    return {
        "none_route": "none",
        "advisory_route": "operations",
        "critical_route": "incident-response",
        "escalated_route": "incident-response",
        "external_delivery_enabled": False,
        "provider_neutral": True,
    }


def _alert(severity: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "delivery_id": "musicclean-routed-slo-123",
        "route": "operations",
        "severity": severity,
        "external_delivery_enabled": False,
    }


def test_repository_configuration():
    assert verify.verify_configuration(ROOT) == ()


def test_none_route():
    assert builder.build_route(_alert("NONE"), _policy())["route"] == "none"


def test_advisory_route():
    assert builder.build_route(_alert("ADVISORY"), _policy())["route"] == "operations"


def test_critical_route():
    assert builder.build_route(_alert("CRITICAL"), _policy())["route"] == "incident-response"


def test_escalated_route():
    assert builder.build_route(_alert("ESCALATED"), _policy())["route"] == "incident-response"


def test_escalated_route_policy_override():
    policy = _policy()
    policy["escalated_route"] = "operations"
    assert builder.build_route(_alert("ESCALATED"), policy)["route"] == "operations"


def test_provider_neutral():
    assert builder.build_route(_alert("ADVISORY"), _policy())["provider_neutral"] is True


def test_external_delivery_disabled():
    assert builder.build_route(_alert("CRITICAL"), _policy())["external_delivery_enabled"] is False


def test_secret_material_rejected():
    route = builder.build_route(_alert("ADVISORY"), _policy())
    route["hmac_secret"] = "secret"
    assert any("hmac_secret" in e for e in verify.verify_route(route))
