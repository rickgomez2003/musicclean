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
    "routed_delivery_slo_route",
    "tools/release/build_recovery_alert_routed_slo_delivery_routed_delivery_slo_route.py",
)
verifier = _load(
    "routed_delivery_slo_route_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_slo_routing.py",
)


def _policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "none_route": "none",
        "advisory_route": "operations",
        "critical_route": "incident-response",
        "escalated_route": "incident-response",
        "external_delivery_enabled": False,
        "provider_neutral": True,
    }


def _alert(
    *,
    alerting: bool = True,
    severity: str = "ADVISORY",
    escalated: bool = False,
    authoritative: bool = True,
) -> dict[str, Any]:
    return {
        "delivery_id": "delivery-1",
        "alert": alerting,
        "severity": severity,
        "escalated": escalated,
        "authoritative": authoritative,
    }


def test_repository_configuration() -> None:
    assert verifier.verify_configuration(ROOT) == ()


def test_no_alert_routes_to_none() -> None:
    route = builder.build_route(
        _alert(alerting=False, severity="NONE"),
        _policy(),
    )
    assert route["logical_route"] == "none"


def test_non_authoritative_routes_to_none() -> None:
    route = builder.build_route(
        _alert(authoritative=False),
        _policy(),
    )
    assert route["logical_route"] == "none"


def test_advisory_routes_to_operations() -> None:
    route = builder.build_route(
        _alert(severity="ADVISORY"),
        _policy(),
    )
    assert route["logical_route"] == "operations"
    assert route["route_reason"] == "advisory_alert"


def test_critical_routes_to_incident_response() -> None:
    route = builder.build_route(
        _alert(severity="CRITICAL"),
        _policy(),
    )
    assert route["logical_route"] == "incident-response"
    assert route["route_reason"] == "critical_alert"


def test_escalated_routes_to_incident_response() -> None:
    route = builder.build_route(
        _alert(severity="ADVISORY", escalated=True),
        _policy(),
    )
    assert route["logical_route"] == "incident-response"
    assert route["route_reason"] == "escalated_alert"


def test_external_delivery_is_disabled() -> None:
    route = builder.build_route(_alert(), _policy())
    assert route["external_delivery_enabled"] is False
    assert route["provider_neutral"] is True


def test_summary_contains_route_state() -> None:
    route = builder.build_route(_alert(), _policy())
    summary = builder.render_summary(route)
    assert "Logical route: `operations`" in summary
    assert "Provider neutral: `True`" in summary


def test_verifier_rejects_secret_material() -> None:
    route = builder.build_route(_alert(), _policy())
    route["hmac_secret"] = "secret"
    assert any("hmac_secret" in error for error in verifier.verify_route(route))
