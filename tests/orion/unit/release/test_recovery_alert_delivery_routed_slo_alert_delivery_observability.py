from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[4]


def load(name: str, relative: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


builder = load(
    "routed_slo_obs", "tools/release/build_recovery_alert_routed_slo_delivery_observability.py"
)
verify = load(
    "routed_slo_obs_verify",
    "tools/release/verify_recovery_alert_delivery_routed_slo_alert_delivery_observability.py",
)


def policy():
    return {"max_attempt_records": 10, "retain_days": 90, "external_export_enabled": False}


def receipt():
    return {
        "delivery_id": "musicclean-routed-slo-123",
        "route": "operations",
        "attempted": True,
        "delivered": True,
        "status": "DELIVERED",
        "http_status": 202,
        "failure_class": None,
        "attempt_count": 2,
        "attempt_history": [
            {
                "attempt": 1,
                "delivered": False,
                "http_status": 503,
                "failure_class": "RETRYABLE_HTTP",
            },
            {"attempt": 2, "delivered": True, "http_status": 202, "failure_class": None},
        ],
    }


def test_repository_configuration():
    assert verify.verify_configuration(ROOT) == ()


def test_summary_metrics():
    report = builder.build_observability(receipt(), policy())
    assert report["metrics"]["attempt_count"] == 2
    assert report["metrics"]["retry_count"] == 1


def test_delivery_id_preserved():
    assert (
        builder.build_observability(receipt(), policy())["delivery_id"]
        == "musicclean-routed-slo-123"
    )


def test_attempt_statuses_bounded():
    r = receipt()
    r["attempt_history"] = [{"attempt": i, "http_status": 503} for i in range(20)]
    r["attempt_count"] = 20
    assert len(builder.build_observability(r, policy())["attempt_statuses"]) == 10


def test_external_export_disabled():
    assert builder.build_observability(receipt(), policy())["external_export_enabled"] is False


def test_summary_contains_metrics():
    text = builder.render_summary(builder.build_observability(receipt(), policy()))
    assert "Attempts: 2" in text and "Retries: 1" in text


def test_secret_material_rejected():
    report = builder.build_observability(receipt(), policy())
    report["webhook_url"] = "https://secret.example.test"
    assert any("webhook_url" in e for e in verify.verify_report(report))
