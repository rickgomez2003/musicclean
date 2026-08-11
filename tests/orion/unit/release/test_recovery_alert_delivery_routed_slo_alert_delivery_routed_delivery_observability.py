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
    "routed_slo_delivery_observability",
    "tools/release/build_recovery_alert_routed_slo_delivery_routed_delivery_observability.py",
)
verify = _load(
    "routed_slo_delivery_observability_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_observability.py",
)


def _policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "max_attempt_records": 10,
        "retain_days": 90,
        "external_export_enabled": False,
    }


def _receipt() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "delivery_id": "delivery-123",
        "logical_route": "operations",
        "severity": "ADVISORY",
        "delivered": True,
        "attempt_count": 2,
        "retry_count": 1,
        "http_status": 204,
        "failure_classification": None,
        "attempts": [
            {
                "attempt": 1,
                "http_status": 503,
                "classification": "http_error",
                "retryable": True,
            },
            {
                "attempt": 2,
                "http_status": 204,
                "classification": "success",
                "retryable": False,
            },
        ],
    }


def test_repository_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_observability_summarizes_terminal_state() -> None:
    report = builder.build_observability(_receipt(), _policy())
    assert report["delivery_id"] == "delivery-123"
    assert report["logical_route"] == "operations"
    assert report["delivered"] is True
    assert report["terminal_http_status"] == 204
    assert report["failure_classification"] is None


def test_observability_tracks_attempts_and_retries() -> None:
    report = builder.build_observability(_receipt(), _policy())
    assert report["attempt_count"] == 2
    assert report["retry_count"] == 1
    assert len(report["attempts"]) == 2


def test_attempt_evidence_is_bounded() -> None:
    receipt = _receipt()
    receipt["attempts"] = [
        {
            "attempt": index + 1,
            "http_status": 503,
            "classification": "http_error",
            "retryable": True,
        }
        for index in range(20)
    ]
    receipt["attempt_count"] = 20
    policy = _policy()
    policy["max_attempt_records"] = 3

    report = builder.build_observability(receipt, policy)
    assert len(report["attempts"]) == 3
    assert report["attempt_records_truncated"] is True


def test_attempt_records_exclude_request_material() -> None:
    receipt = _receipt()
    receipt["attempts"][0]["request_headers"] = {"Authorization": "secret"}
    receipt["attempts"][0]["endpoint_url"] = "https://secret.invalid"

    report = builder.build_observability(receipt, _policy())
    assert "request_headers" not in report["attempts"][0]
    assert "endpoint_url" not in report["attempts"][0]


def test_external_export_is_disabled() -> None:
    report = builder.build_observability(_receipt(), _policy())
    assert report["external_export_enabled"] is False


def test_summary_contains_delivery_metrics() -> None:
    report = builder.build_observability(_receipt(), _policy())
    summary = builder.render_summary(report)
    assert "Attempts: `2`" in summary
    assert "Retries: `1`" in summary
    assert "Terminal HTTP status: `204`" in summary


def test_report_is_secret_safe() -> None:
    report = builder.build_observability(_receipt(), _policy())
    assert builder.verify_secret_safe(report) == ()
    assert verify.verify_report(report) == ()


def test_verifier_rejects_secret_material() -> None:
    report = builder.build_observability(_receipt(), _policy())
    report["hmac_secret"] = "secret"
    assert any("hmac_secret" in error for error in verify.verify_report(report))
