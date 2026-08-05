"""Verify recovery-objective policy, workflow integration, and SLO reports."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    policy_path = root / "release" / "recovery-slos.toml"
    try:
        with policy_path.open("rb") as stream:
            document = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return (f"unable to load recovery SLO policy: {exc}",)

    recovery = document.get("recovery")
    if not isinstance(recovery, dict):
        return ("recovery SLO policy is missing",)

    if recovery.get("schema_version") != 1:
        errors.append("recovery SLO schema version must be 1")
    if recovery.get("status_levels") != ["PASS", "WARN", "FAIL"]:
        errors.append("recovery SLO status levels must be PASS/WARN/FAIL")

    duration = recovery.get("duration_seconds")
    age = recovery.get("successful_drill_age_days")
    ratio = recovery.get("success_ratio")

    if not isinstance(duration, dict):
        errors.append("recovery duration objective is missing")
    elif not (
        isinstance(duration.get("warning"), int)
        and isinstance(duration.get("objective"), int)
        and 0 < duration["warning"] < duration["objective"]
    ):
        errors.append("recovery duration thresholds are invalid")

    if not isinstance(age, dict):
        errors.append("successful drill age objective is missing")
    elif not (
        isinstance(age.get("warning"), int)
        and isinstance(age.get("objective"), int)
        and 0 < age["warning"] < age["objective"]
    ):
        errors.append("successful drill age thresholds are invalid")

    if not isinstance(ratio, dict):
        errors.append("recovery success ratio objective is missing")
    else:
        warning = ratio.get("warning")
        objective = ratio.get("objective")
        samples = ratio.get("minimum_samples")
        if not (
            isinstance(warning, (int, float))
            and isinstance(objective, (int, float))
            and 0 <= objective <= warning <= 1
        ):
            errors.append("recovery success ratio thresholds are invalid")
        if not isinstance(samples, int) or samples < 1:
            errors.append("recovery success ratio minimum_samples is invalid")

    workflow = (root / ".github" / "workflows" / "orion-recovery-drill.yml").read_text(
        encoding="utf-8"
    )

    required = (
        "Evaluate recovery SLOs",
        "evaluate_recovery_slos.py",
        "recovery-slo-report.json",
        "Verify recovery SLO report",
        "verify_recovery_slos.py",
        "actions/upload-artifact@v4",
        "contents: read",
        "id-token: write",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"recovery drill workflow missing SLO integration {fragment}")

    complete = workflow.find("Complete recovery drill")
    evaluate = workflow.find("Evaluate recovery SLOs")
    verify = workflow.find("Verify recovery SLO report")
    upload = workflow.find("Upload recovery drill evidence")
    positions = [complete, evaluate, verify, upload]
    if any(position == -1 for position in positions):
        errors.append("recovery SLO workflow ordering cannot be verified")
    elif positions != sorted(positions):
        errors.append("recovery SLO workflow ordering is invalid")

    forbidden = (
        "contents: write",
        "gh release edit",
        "gh release create",
        "gh release upload",
        "git tag",
        "git push",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "--admin",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"recovery SLO workflow contains forbidden pattern {fragment}")

    return tuple(errors)


def verify_report(path: Path) -> tuple[str, ...]:
    errors: list[str] = []
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load recovery SLO report: {exc}",)

    if not isinstance(report, dict):
        return ("recovery SLO report must be an object",)

    for field in ("schema_version", "evaluated_at", "status", "metrics"):
        if field not in report:
            errors.append(f"recovery SLO report missing field {field}")

    if report.get("schema_version") != 1:
        errors.append("recovery SLO report schema version must be 1")
    if report.get("status") not in {"PASS", "WARN", "FAIL"}:
        errors.append("recovery SLO report status is invalid")
    if not isinstance(report.get("metrics"), dict):
        errors.append("recovery SLO report metrics must be an object")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())
    if args.report is not None:
        errors.extend(verify_report(args.report))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.report is None:
        print("recovery objectives and SLO policy verified")
    else:
        print(f"recovery SLO report verified: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
