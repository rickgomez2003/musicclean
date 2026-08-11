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
    "routed_delivery_observability_builder",
    "tools/release/build_recovery_alert_routed_slo_delivery_routed_delivery_routed_delivery_observability.py",
)
verifier = _load(
    "routed_delivery_observability_verifier",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_routed_delivery_observability.py",
)


def _receipt(
    *,
    status: str = "DELIVERED",
    attempts: int = 2,
    failure: str | None = None,
) -> dict[str, Any]:
    records = []
    for index in range(1, attempts + 1):
        delivered = index == attempts and status == "DELIVERED"
        records.append(
            {
                "attempt": index,
                "delivery_id": "a" * 64,
                "status": "DELIVERED" if delivered else "FAILED",
                "http_status": 202 if delivered else 503,
                "failure_classification": None if delivered else "http_error",
                "retryable": index < attempts,
            }
        )

    return {
        "schema_version": 2,
        "logical_route": "operations",
        "delivery_id": "a" * 64,
        "delivery_status": status,
        "attempt_count": attempts,
        "retry_count": max(0, attempts - 1),
        "attempts": records,
        "http_status": 202 if status == "DELIVERED" else 503,
        "failure_classification": failure,
    }


def test_repository_configuration() -> None:
    assert verifier.verify_configuration(ROOT) == ()


def test_terminal_state() -> None:
    report = builder.build_observability(_receipt())
    assert report["delivery_status"] == "DELIVERED"
    assert report["terminal_http_status"] == 202


def test_attempts_and_retries() -> None:
    report = builder.build_observability(_receipt(attempts=3))
    assert report["attempt_count"] == 3
    assert report["retry_count"] == 2
    assert report["had_retries"] is True


def test_transport_failure() -> None:
    report = builder.build_observability(_receipt(status="FAILED", failure="transport_error"))
    assert report["transport_failure"] is True


def test_attempt_evidence_is_bounded() -> None:
    report = builder.build_observability(
        _receipt(attempts=5),
        max_attempt_records=3,
    )
    assert len(report["attempts"]) == 3


def test_request_material_is_excluded() -> None:
    receipt = _receipt()
    receipt["attempts"][0]["request_headers"] = {"Authorization": "secret"}
    report = builder.build_observability(receipt)
    assert "request_headers" not in report["attempts"][0]


def test_external_export_is_disabled() -> None:
    assert builder.build_observability(_receipt())["external_export_enabled"] is False


def test_summary_contains_metrics() -> None:
    summary = builder.render_summary(builder.build_observability(_receipt()))
    assert "Delivery status" in summary
    assert "Attempts" in summary
    assert "Retries" in summary


def test_report_is_secret_safe() -> None:
    assert verifier.verify_report(builder.build_observability(_receipt())) == ()


def test_verifier_rejects_secret_material() -> None:
    report = builder.build_observability(_receipt())
    report["endpoint_url"] = "https://example.invalid"
    assert any("endpoint_url" in error for error in verifier.verify_report(report))
