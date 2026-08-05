"""Verify recovery SLO alerting policy, workflow integration, and alert records."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    policy_path = root / "release" / "recovery-alerting.toml"
    try:
        with policy_path.open("rb") as stream:
            document = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return (f"unable to load recovery alerting policy: {exc}",)

    alerting = document.get("alerting")
    if not isinstance(alerting, dict):
        return ("recovery alerting policy is missing",)

    if alerting.get("schema_version") != 1:
        errors.append("recovery alerting schema version must be 1")
    if alerting.get("suppression_window_hours") != 24:
        errors.append("recovery alert suppression window must be 24 hours")
    if alerting.get("consecutive_failure_escalation") != 2:
        errors.append("recovery escalation threshold must be 2 failures")
    if alerting.get("provider") != "github-summary":
        errors.append("recovery alert provider must be github-summary")
    if alerting.get("external_delivery_enabled") is not False:
        errors.append("external recovery alert delivery must remain disabled")

    severity = alerting.get("severity")
    expected_severity = {
        "warn": "ADVISORY",
        "fail": "CRITICAL",
        "worsening": "ADVISORY",
        "escalated": "ESCALATED",
    }
    if severity != expected_severity:
        errors.append("recovery alert severity mapping is invalid")

    workflow_path = root / ".github" / "workflows" / "orion-recovery-drill.yml"
    workflow = workflow_path.read_text(encoding="utf-8")

    required = (
        "Build recovery SLO alert",
        "build_recovery_alert.py",
        "recovery-slo-alert.json",
        "recovery-slo-alert-summary.md",
        "GITHUB_STEP_SUMMARY",
        "Verify recovery SLO alert",
        "verify_recovery_slo_alerting.py",
        "actions: read",
        "contents: read",
        "id-token: write",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"recovery workflow missing alerting integration {fragment}")

    ordered = (
        "Verify recovery SLO report",
        "Verify recovery SLO history",
        "Build recovery SLO alert",
        "Verify recovery SLO alert",
        "Publish recovery SLO summary",
        "Upload recovery drill evidence",
    )
    positions = [workflow.find(step) for step in ordered]
    if any(position == -1 for position in positions):
        errors.append("recovery alert workflow ordering cannot be verified")
    elif positions != sorted(positions):
        errors.append("recovery alert workflow ordering is invalid")

    forbidden = (
        "contents: write",
        "issues: write",
        "pull-requests: write",
        "gh release edit",
        "gh release create",
        "gh release upload",
        "git tag",
        "git push",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "SLACK_",
        "PAGERDUTY_",
        "TEAMS_",
        "WEBHOOK",
        "--admin",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"recovery alert workflow contains forbidden pattern {fragment}")

    return tuple(errors)


def verify_alert(path: Path) -> tuple[str, ...]:
    try:
        alert = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load recovery SLO alert: {exc}",)

    if not isinstance(alert, dict):
        return ("recovery SLO alert must be an object",)

    errors: list[str] = []
    required = (
        "schema_version",
        "evaluated_at",
        "alert_required",
        "severity",
        "reasons",
        "slo_status",
        "duration_trend",
        "consecutive_failures",
        "escalation_threshold",
        "escalated",
        "suppression_window_hours",
        "provider",
        "external_delivery_enabled",
    )
    for field in required:
        if field not in alert:
            errors.append(f"recovery SLO alert missing field {field}")

    if alert.get("schema_version") != 1:
        errors.append("recovery SLO alert schema version must be 1")

    severity = alert.get("severity")
    if severity not in {None, "ADVISORY", "CRITICAL", "ESCALATED"}:
        errors.append("recovery SLO alert severity is invalid")

    if alert.get("alert_required") is False and severity is not None:
        errors.append("healthy recovery SLO alert cannot have severity")
    if alert.get("escalated") is True and severity != "ESCALATED":
        errors.append("escalated recovery SLO alert must use ESCALATED severity")
    if alert.get("external_delivery_enabled") is not False:
        errors.append("external delivery must remain disabled")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alert", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())
    if args.alert is not None:
        errors.extend(verify_alert(args.alert))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.alert is None:
        print("recovery SLO alerting and escalation policy verified")
    else:
        print(f"recovery SLO alert verified: {args.alert}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
