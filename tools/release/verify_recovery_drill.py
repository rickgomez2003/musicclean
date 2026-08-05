"""Verify recovery drill policy and drill records."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    policy_path = root / "release" / "recovery-drill.toml"
    try:
        with policy_path.open("rb") as stream:
            document = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return (f"unable to load recovery drill policy: {exc}",)

    drill = document.get("drill")
    expected = {
        "schema_version": 1,
        "environment": "release-archive-export",
        "authentication": "github-oidc",
        "schedule": "weekly",
        "require_known_archive": True,
        "verify_before_extract": True,
        "verify_restored_evidence": True,
        "record_elapsed_seconds": True,
        "record_restore_receipt": True,
        "upload_drill_record": True,
        "preserve_github_release": True,
        "no_automatic_republish": True,
    }
    if drill != expected:
        errors.append("recovery drill policy does not match expected safe values")

    workflow_path = root / ".github" / "workflows" / "orion-recovery-drill.yml"
    workflow = workflow_path.read_text(encoding="utf-8")

    required = (
        "workflow_dispatch:",
        "schedule:",
        "cron:",
        "contents: read",
        "id-token: write",
        "name: release-archive-export",
        "resolve_recovery_drill_target.py",
        "recovery_drill_record.py start",
        "Download and verify durable archive identity",
        "Verify downloaded archive bundle",
        "Extract verified archive",
        "--extract-verified",
        "Verify restored audit evidence",
        "verify_archive_restore.py",
        "recovery_drill_record.py complete",
        "recovery_drill_record.py fail",
        "verify_recovery_drill.py",
        "actions/upload-artifact@v4",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"recovery drill workflow missing {fragment}")

    ordered_steps = (
        "Download and verify durable archive identity",
        "Verify downloaded archive bundle",
        "Extract verified archive",
        "Verify restored audit evidence",
        "Verify restore receipt",
        "Complete recovery drill",
        "Verify recovery drill record",
    )
    positions = [workflow.find(step) for step in ordered_steps]
    if any(position == -1 for position in positions):
        errors.append("recovery drill workflow is missing ordered recovery steps")
    elif positions != sorted(positions):
        errors.append("recovery drill workflow does not preserve verification order")

    forbidden = (
        "contents: write",
        "gh release edit",
        "gh release create",
        "gh release upload",
        "gh release delete",
        "git tag",
        "git push",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "--admin",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"recovery drill workflow contains forbidden pattern {fragment}")

    return tuple(errors)


def verify_record(path: Path) -> tuple[str, ...]:
    errors: list[str] = []
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load recovery drill record: {exc}",)

    if not isinstance(record, dict):
        return ("recovery drill record must be an object",)

    required = (
        "schema_version",
        "drill_id",
        "repository",
        "run_id",
        "tag",
        "retention_class",
        "started_at",
        "completed_at",
        "elapsed_seconds",
        "status",
        "restore_receipt",
        "failure_reason",
    )
    for field in required:
        if field not in record:
            errors.append(f"recovery drill record missing field {field}")

    if record.get("schema_version") != 1:
        errors.append("recovery drill schema version must be 1")
    if record.get("retention_class") not in {"operational", "long-term"}:
        errors.append("recovery drill retention class is invalid")
    if record.get("status") not in {"PASS", "FAIL"}:
        errors.append("recovery drill status must be PASS or FAIL")

    elapsed = record.get("elapsed_seconds")
    if not isinstance(elapsed, (int, float)) or elapsed < 0:
        errors.append("recovery drill elapsed_seconds must be non-negative")

    status = record.get("status")
    if status == "PASS":
        receipt = record.get("restore_receipt")
        if not isinstance(receipt, dict):
            errors.append("passing recovery drill must contain restore receipt")
        else:
            for field in ("remote_verified", "download_verified", "safe_extract"):
                if receipt.get(field) is not True:
                    errors.append(f"passing recovery drill restore receipt must prove {field}")
        if record.get("failure_reason") is not None:
            errors.append("passing recovery drill cannot contain failure reason")

    if status == "FAIL" and not record.get("failure_reason"):
        errors.append("failed recovery drill must contain failure reason")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())
    if args.record is not None:
        errors.extend(verify_record(args.record))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.record is None:
        print("recovery drill automation policy verified")
    else:
        print(f"recovery drill record verified: {args.record}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
