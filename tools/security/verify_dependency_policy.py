"""Verify MusicClean dependency and vulnerability policy configuration."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_SEVERITIES = {"low", "moderate", "high", "critical"}


def _load_policy(root: Path) -> dict[str, Any]:
    path = root / "security" / "dependency-vulnerability-policy.toml"
    with path.open("rb") as stream:
        return tomllib.load(stream)


def verify(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []
    policy_doc = _load_policy(root)
    policy = policy_doc.get("policy")
    exceptions = policy_doc.get("exceptions")

    if not isinstance(policy, dict):
        return ("dependency policy table is missing",)
    if not isinstance(exceptions, dict):
        errors.append("dependency exceptions table is missing")
        exceptions = {}

    severity = policy.get("pull_request_fail_severity")
    if severity not in ALLOWED_SEVERITIES:
        errors.append("pull_request_fail_severity is invalid")

    if policy.get("runtime_audit_required") is not True:
        errors.append("runtime dependency audit must be required")

    maximum_exception_days = policy.get("maximum_exception_days")
    if (
        not isinstance(maximum_exception_days, int)
        or maximum_exception_days <= 0
        or maximum_exception_days > 30
    ):
        errors.append("maximum_exception_days must be between 1 and 30")

    if policy.get("require_exception_owner") is not True:
        errors.append("vulnerability exceptions must require an owner")

    if policy.get("require_exception_reason") is not True:
        errors.append("vulnerability exceptions must require a reason")

    vulnerability_ids = exceptions.get("vulnerability_ids")
    if not isinstance(vulnerability_ids, list):
        errors.append("vulnerability_ids must be a list")

    workflow = (root / ".github" / "workflows" / "orion-dependency-security.yml").read_text(
        encoding="utf-8"
    )

    required = (
        "actions/dependency-review-action@v4",
        "fail-on-severity: high",
        "fail-on-scopes: runtime",
        "pip-audit",
        "--local",
        "--skip-editable",
        "orion-runtime",
        "opentelemetry",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"dependency-security workflow missing {fragment}")

    if "permissions:\n  contents: read" not in workflow:
        errors.append("dependency-security workflow must remain read-only")

    return tuple(errors)


def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("dependency and vulnerability policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
