"""Verify Orion recovery alert delivery resilience controls."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify(root: Path = ROOT) -> tuple[str, ...]:
    workflow = (
        root / ".github" / "workflows" / "orion-recovery-drill.yml"
    ).read_text(encoding="utf-8")
    delivery = (
        root / "tools" / "release" / "deliver_recovery_alert.py"
    ).read_text(encoding="utf-8")

    errors: list[str] = []
    required_workflow = (
        "external-alert-delivery:",
        "needs: recovery-drill",
        "name: recovery-alert-delivery",
        "actions/download-artifact@v4",
        "actions/upload-artifact@v4",
    )
    for fragment in required_workflow:
        if fragment not in workflow:
            errors.append(f"resilient delivery workflow missing {fragment}")

    required_delivery = (
        "_retryable_status",
        "_backoff_seconds",
        "retry_statuses",
        "retry_server_errors",
        "attempt_history",
        "transient-http",
        "terminal-http",
        "transient-network",
    )
    for fragment in required_delivery:
        if fragment not in delivery:
            errors.append(f"resilient delivery implementation missing {fragment}")

    return tuple(errors)


def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("recovery alert delivery resilience policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
