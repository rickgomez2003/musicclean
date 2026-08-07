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
    "musicclean_routed_delivery_observability",
    "tools/release/build_recovery_alert_routed_delivery_observability.py",
)
verify = _load(
    "musicclean_routed_delivery_observability_verify",
    "tools/release/verify_recovery_alert_delivery_routed_delivery_observability.py",
)


def _receipt(
    delivery_id: str,
    route: str,
    delivered: bool,
    attempts: int,
    failure_class: str | None = None,
    elapsed: float = 1.0,
    delivered_at: str = "2026-08-07T00:00:00+00:00",
) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "delivered_at": delivered_at,
        "elapsed_seconds": elapsed,
        "route_required": True,
        "delivered": delivered,
        "route": route,
        "severity": "CRITICAL",
        "status_code": 200 if delivered else 503,
        "delivery_id": delivery_id,
        "failure_class": failure_class,
        "attempts": attempts,
        "attempt_history": [],
    }


def test_repository_observability_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_observation_aggregates_success_and_retries() -> None:
    history = [
        _receipt("a", "operations", True, 1, elapsed=1.0),
        _receipt("b", "operations", False, 4, "retryable-http", 8.0, "2026-08-07T00:01:00+00:00"),
    ]
    current = _receipt(
        "c", "incident-response", True, 3, elapsed=3.0, delivered_at="2026-08-07T00:02:00+00:00"
    )
    observation = builder.build_observation(current, history, {"history_limit": 52})
    assert observation["sample_count"] == 3
    assert observation["success_count"] == 2
    assert observation["success_rate"] == 2 / 3
    assert observation["total_attempts"] == 8
    assert observation["total_retries"] == 5
    assert observation["retry_rate"] == 5 / 8
    assert observation["max_attempts"] == 4


def test_observation_tracks_routes_and_failures() -> None:
    history = [
        _receipt("a", "operations", False, 1, "terminal-http"),
        _receipt("b", "operations", False, 2, "transport"),
    ]
    current = _receipt("c", "incident-response", False, 4, "retryable-http")
    observation = builder.build_observation(current, history, {"history_limit": 52})
    assert observation["route_counts"] == {"incident-response": 1, "operations": 2}
    assert observation["terminal_http_failure_count"] == 1
    assert observation["transport_failure_count"] == 1
    assert observation["retryable_http_failure_count"] == 1


def test_history_is_deduplicated_by_delivery_id() -> None:
    history = [
        _receipt("same", "operations", False, 4),
        _receipt("same", "operations", True, 2, delivered_at="2026-08-07T00:01:00+00:00"),
    ]
    current = _receipt("current", "operations", True, 1, delivered_at="2026-08-07T00:02:00+00:00")
    observation = builder.build_observation(current, history, {"history_limit": 52})
    assert observation["sample_count"] == 2
    assert observation["success_count"] == 2


def test_history_is_bounded() -> None:
    history = [
        _receipt(
            f"id-{index}", "operations", True, 1, delivered_at=f"2026-08-07T00:{index:02d}:00+00:00"
        )
        for index in range(10)
    ]
    current = _receipt("current", "operations", True, 1, delivered_at="2026-08-07T01:00:00+00:00")
    observation = builder.build_observation(current, history, {"history_limit": 4})
    assert observation["sample_count"] == 4
    assert observation["history_limit"] == 4


def test_summary_contains_route_and_failure_sections() -> None:
    observation = builder.build_observation(
        _receipt("current", "operations", True, 1), [], {"history_limit": 52}
    )
    summary = builder.render_summary(observation)
    assert "Routed Recovery Alert Delivery Observability" in summary
    assert "### Routes" in summary
    assert "### Failure Classes" in summary


def test_observability_rejects_secret_material() -> None:
    observation = builder.build_observation(
        _receipt("current", "operations", True, 1), [], {"history_limit": 52}
    )
    observation["endpoint_url"] = "https://secret.example.test"
    errors = verify.verify_observation(observation)
    assert any("endpoint_url" in error for error in errors)
