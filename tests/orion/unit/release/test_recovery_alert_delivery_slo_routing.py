from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

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
    "musicclean_delivery_slo_route",
    "tools/release/build_recovery_alert_delivery_slo_route.py",
)
verify = _load(
    "musicclean_delivery_slo_route_verify",
    "tools/release/verify_recovery_alert_delivery_slo_routing.py",
)


def _policy() -> dict[str, object]:
    return {
        "schema_version": 1,
        "default_route": "operations",
        "escalation_route": "incident-response",
        "consecutive_nonpass_escalation": 3,
        "escalate_worsening_critical": True,
        "external_delivery_enabled": False,
        "routes": {
            "advisory": "operations",
            "critical": "operations",
            "escalated": "incident-response",
        },
    }


def test_repository_routing_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_no_alert_produces_no_route() -> None:
    route = builder.build_route(
        {
            "alert_required": False,
            "severity": "NONE",
            "consecutive_warn_fail": 0,
            "trend_status": "stable",
        },
        _policy(),
    )
    assert route["route_required"] is False
    assert route["route"] == "none"


def test_advisory_routes_to_operations() -> None:
    route = builder.build_route(
        {
            "alert_required": True,
            "severity": "ADVISORY",
            "consecutive_warn_fail": 1,
            "trend_status": "stable",
        },
        _policy(),
    )
    assert route["route"] == "operations"
    assert route["escalation_required"] is False


def test_critical_routes_to_operations() -> None:
    route = builder.build_route(
        {
            "alert_required": True,
            "severity": "CRITICAL",
            "consecutive_warn_fail": 1,
            "trend_status": "stable",
        },
        _policy(),
    )
    assert route["route"] == "operations"


def test_escalated_routes_to_incident_response() -> None:
    route = builder.build_route(
        {
            "alert_required": True,
            "severity": "ESCALATED",
            "consecutive_warn_fail": 2,
            "trend_status": "stable",
        },
        _policy(),
    )
    assert route["route"] == "incident-response"


def test_consecutive_nonpass_forces_escalation_route() -> None:
    route = builder.build_route(
        {
            "alert_required": True,
            "severity": "ADVISORY",
            "consecutive_warn_fail": 3,
            "trend_status": "stable",
        },
        _policy(),
    )
    assert route["escalation_required"] is True
    assert route["route"] == "incident-response"


def test_worsening_critical_forces_escalation_route() -> None:
    route = builder.build_route(
        {
            "alert_required": True,
            "severity": "CRITICAL",
            "consecutive_warn_fail": 1,
            "trend_status": "worsening",
        },
        _policy(),
    )
    assert route["escalation_required"] is True
    assert route["route"] == "incident-response"
