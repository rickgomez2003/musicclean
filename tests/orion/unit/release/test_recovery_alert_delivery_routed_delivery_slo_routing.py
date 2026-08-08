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
    "musicclean_routed_delivery_slo_route",
    "tools/release/build_recovery_alert_routed_delivery_slo_route.py",
)
verify = _load(
    "musicclean_routed_delivery_slo_route_verify",
    "tools/release/verify_recovery_alert_delivery_routed_delivery_slo_routing.py",
)


def _policy() -> dict[str, Any]:
    return {
        "severity_routes": {
            "NONE": "none",
            "ADVISORY": "operations",
            "CRITICAL": "incident-response",
            "ESCALATED": "incident-response",
        },
        "escalated_route": "incident-response",
        "external_delivery_enabled": False,
    }


def _alert(
    *,
    required: bool = True,
    severity: str = "ADVISORY",
    escalated: bool = False,
) -> dict[str, Any]:
    return {
        "alert_required": required,
        "severity": severity,
        "escalated": escalated,
        "current_route": "operations",
        "current_severity": "CRITICAL",
    }


def test_repository_routed_delivery_slo_routing_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_no_alert_routes_to_none() -> None:
    route = builder.build_route(
        _alert(required=False, severity="NONE"),
        _policy(),
    )
    assert route["route_required"] is False
    assert route["route"] == "none"


def test_advisory_routes_to_operations() -> None:
    route = builder.build_route(
        _alert(severity="ADVISORY"),
        _policy(),
    )
    assert route["route_required"] is True
    assert route["route"] == "operations"


def test_critical_routes_to_incident_response() -> None:
    route = builder.build_route(
        _alert(severity="CRITICAL"),
        _policy(),
    )
    assert route["route"] == "incident-response"


def test_escalated_routes_to_incident_response() -> None:
    route = builder.build_route(
        _alert(severity="ESCALATED", escalated=True),
        _policy(),
    )
    assert route["route"] == "incident-response"
    assert route["escalated"] is True


def test_escalated_flag_overrides_advisory_route() -> None:
    route = builder.build_route(
        _alert(severity="ADVISORY", escalated=True),
        _policy(),
    )
    assert route["route"] == "incident-response"


def test_source_route_context_is_preserved() -> None:
    route = builder.build_route(
        _alert(severity="ADVISORY"),
        _policy(),
    )
    assert route["source_route"] == "operations"


def test_external_delivery_remains_disabled() -> None:
    route = builder.build_route(
        _alert(severity="CRITICAL"),
        _policy(),
    )
    assert route["external_delivery_enabled"] is False


def test_route_verifier_rejects_secret_material() -> None:
    route = builder.build_route(
        _alert(severity="CRITICAL"),
        _policy(),
    )
    route["webhook_url"] = "https://secret.example.test"

    errors = verify.verify_route(route)

    assert any("webhook_url" in error for error in errors)
