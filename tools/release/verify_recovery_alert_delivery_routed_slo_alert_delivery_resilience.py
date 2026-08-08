"""Verify routed SLO alert delivery resilience policy and invariants."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []
    with (root / "release/recovery-alerting.toml").open("rb") as stream:
        document = tomllib.load(stream)
    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        return ("recovery alerting policy is missing",)
    expected = {
        "schema_version": 1,
        "max_attempts": 3,
        "base_delay_seconds": 1.0,
        "max_delay_seconds": 4.0,
        "retryable_http_statuses": [408, 425, 429, 500, 502, 503, 504],
        "retry_transport_errors": True,
        "preserve_delivery_id": True,
    }
    if alerting.get("routed_slo_alert_delivery_resilience") != expected:
        errors.append("routed SLO alert delivery resilience policy is invalid")
    workflow = (root / ".github/workflows/orion-recovery-drill.yml").read_text(encoding="utf-8")
    if "--policy release/recovery-alerting.toml" not in workflow:
        errors.append("routed SLO alert delivery workflow does not pass resilience policy")
    for forbidden in (
        "GITHUB_ENV",
        "RECOVERY_ROUTED_WEBHOOK_URL",
        "RECOVERY_ROUTED_HMAC_SECRET",
        "contents: write",
        "actions: write",
        "packages: write",
        "pull-requests: write",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    ):
        if forbidden in workflow:
            errors.append(f"routed SLO alert delivery resilience workflow contains {forbidden}")
    return tuple(errors)


def main() -> int:
    errors = verify_configuration()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("recovery alert routed SLO alert delivery resilience policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
