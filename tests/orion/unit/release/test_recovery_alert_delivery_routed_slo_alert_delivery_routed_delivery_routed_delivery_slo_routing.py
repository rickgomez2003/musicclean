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
    "routed_delivery_slo_route_builder",
    "tools/release/"
    "build_recovery_alert_routed_slo_delivery_routed_delivery_"
    "routed_delivery_slo_route.py",
)
verifier = _load(
    "routed_delivery_slo_route_verifier",
    "tools/release/"
    "verify_recovery_alert_delivery_routed_slo_alert_delivery_"
    "routed_delivery_routed_delivery_slo_routing.py",
)


def _alert(
    state: str,
    *,
    should_alert: bool = True,
    authoritative: bool = True,
    severity: str = "warning",
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "alert_state": state,
        "severity": severity,
        "should_alert": should_alert,
        "slo_authoritative": authoritative,
    }


def test_repository_configuration() -> None:
    assert verifier.verify_configuration(ROOT) == ()


def test_no_alert_routes_to_none() -> None:
    report = builder.build_route(
        _alert(
            "NONE",
            should_alert=False,
            severity="none",
        )
    )
    assert report["logical_route"] == "none"


def test_non_authoritative_routes_to_none() -> None:
    report = builder.build_route(
        _alert(
            "NON_AUTHORITATIVE",
            should_alert=False,
            authoritative=False,
            severity="none",
        )
    )
    assert report["logical_route"] == "none"


def test_advisory_routes_to_operations() -> None:
    report = builder.build_route(_alert("ADVISORY"))
    assert report["logical_route"] == "operations"


def test_critical_routes_to_incident_response() -> None:
    report = builder.build_route(
        _alert(
            "CRITICAL",
            severity="critical",
        )
    )
    assert report["logical_route"] == "incident_response"


def test_escalated_routes_to_incident_response() -> None:
    report = builder.build_route(
        _alert(
            "ESCALATED",
            severity="critical",
        )
    )
    assert report["logical_route"] == "incident_response"


def test_external_delivery_is_disabled() -> None:
    report = builder.build_route(_alert("ADVISORY"))
    assert report["external_delivery_enabled"] is False


def test_summary_contains_route_state() -> None:
    report = builder.build_route(_alert("ADVISORY"))
    summary = builder.render_summary(report)

    assert "Logical route" in summary
    assert "Route reason" in summary
    assert "Alert state" in summary


def test_report_is_secret_safe() -> None:
    report = builder.build_route(_alert("ADVISORY"))
    assert verifier.verify_report(report) == ()


def test_verifier_rejects_secret_material() -> None:
    report = builder.build_route(_alert("ADVISORY"))
    report["endpoint_url"] = "https://example.invalid"

    assert any("endpoint_url" in error for error in verifier.verify_report(report))
