from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_FRAGMENTS = (
    "endpoint_url",
    "hmac_secret",
    "signature",
    "authorization",
    "webhook_url",
    "request_headers",
    "https://",
    "http://",
)


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    with (root / "release/recovery-alerting.toml").open("rb") as stream:
        document = tomllib.load(stream)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        return ("recovery alerting policy is missing",)

    expected = {
        "schema_version": 1,
        "max_history_entries": 20,
        "minimum_trend_samples": 4,
        "trend_window_size": 3,
        "external_export_enabled": False,
        "provider_neutral": True,
        "read_only": True,
        "deduplicated": True,
    }

    if (
        alerting.get("routed_slo_alert_delivery_routed_delivery_routed_delivery_slo_history")
        != expected
    ):
        errors.append("routed-delivery SLO history policy is invalid")

    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")

    for fragment in (
        "Build routed recovery SLO alert delivery routed delivery routed delivery SLO history",
        "Analyze routed recovery SLO alert delivery routed delivery routed delivery SLO trends",
        (
            "Verify routed recovery SLO alert delivery routed delivery "
            "routed delivery SLO history and trends"
        ),
        "build_recovery_alert_routed_slo_delivery_routed_delivery_routed_delivery_slo_history.py",
        "analyze_recovery_alert_routed_slo_delivery_routed_delivery_routed_delivery_slo_trends.py",
        "verify_recovery_alert_delivery_routed_slo_alert_delivery_routed_delivery_routed_delivery_slo_history.py",
        "recovery-alert-routed-slo-delivery-routed-delivery-slo-history.json",
        "recovery-alert-routed-slo-delivery-routed-delivery-slo-trends.json",
    ):
        if fragment not in workflow:
            errors.append(f"workflow missing {fragment}")

    return tuple(errors)


def _check_secret_safe(
    document: Any,
    errors: list[str],
) -> None:
    serialized = json.dumps(document, sort_keys=True).lower()
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment in serialized:
            errors.append(f"history/trend evidence contains forbidden material {fragment}")


def verify_history(history: Any) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(history, list):
        return ("history must be a JSON array",)

    if len(history) > 20:
        errors.append("history exceeds configured retention bound")

    seen: set[str] = set()
    for entry in history:
        if not isinstance(entry, dict):
            errors.append("history entries must be JSON objects")
            continue

        history_id = entry.get("history_id")
        if not isinstance(history_id, str):
            errors.append("history entry is missing history_id")
        elif history_id in seen:
            errors.append("history contains duplicate entries")
        else:
            seen.add(history_id)

    _check_secret_safe(history, errors)
    return tuple(errors)


def verify_trends(report: Any) -> tuple[str, ...]:
    errors: list[str] = []

    if not isinstance(report, dict):
        return ("trend report must be a JSON object",)

    if report.get("schema_version") != 1:
        errors.append("trend schema_version must be 1")

    if report.get("overall_trend") not in {
        "IMPROVING",
        "STABLE",
        "WORSENING",
        "INSUFFICIENT_HISTORY",
    }:
        errors.append("overall_trend is invalid")

    metrics = report.get("metrics")
    if not isinstance(metrics, dict):
        errors.append("trend metrics must be an object")

    if report.get("external_export_enabled") is not False:
        errors.append("external export must remain disabled")

    if report.get("provider_neutral") is not True:
        errors.append("trend evidence must remain provider-neutral")

    _check_secret_safe(report, errors)
    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path)
    parser.add_argument("--trend", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())

    if args.history is not None:
        errors.extend(verify_history(json.loads(args.history.read_text(encoding="utf-8"))))

    if args.trend is not None:
        errors.extend(verify_trends(json.loads(args.trend.read_text(encoding="utf-8"))))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        "recovery alert routed SLO alert delivery routed delivery "
        "routed delivery SLO history and trend policy verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
