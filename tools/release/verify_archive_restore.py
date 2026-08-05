"""Verify MusicClean archive restore and disaster recovery policy."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    path = root / "release" / "restore.toml"
    try:
        with path.open("rb") as stream:
            document = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return (f"unable to load archive restore policy: {exc}",)

    restore = document.get("restore")
    if not isinstance(restore, dict):
        return ("archive restore policy table is missing",)

    expected = {
        "schema_version": 1,
        "provider": "aws-s3",
        "environment": "release-archive-export",
        "authentication": "github-oidc",
        "default_prefix": "musicclean/releases",
        "verify_remote_sha256_metadata": True,
        "verify_archive_manifest": True,
        "safe_extract": True,
        "verify_restored_evidence": True,
        "upload_restore_receipt": True,
        "preserve_github_release": True,
        "no_automatic_republish": True,
    }
    if restore != expected:
        errors.append("archive restore policy does not match expected safe values")

    workflow = (root / ".github" / "workflows" / "orion-archive-restore.yml").read_text(
        encoding="utf-8"
    )

    required = (
        "workflow_dispatch:",
        "contents: read",
        "id-token: write",
        "name: release-archive-export",
        "aws-actions/configure-aws-credentials@v5",
        "role-to-assume: ${{ secrets.AWS_ARCHIVE_ROLE_ARN }}",
        "restore_release_archive.py",
        "verify_retention_archival.py",
        "verify_audit_evidence.py",
        "verify_archive_restore.py",
        "actions/upload-artifact@v4",
        "retention-days: 90",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"archive restore workflow missing {fragment}")

    ordered_steps = (
        "Download and verify durable archive identity",
        "Verify downloaded archive bundle",
        "Extract verified archive",
        "Verify restored audit evidence",
        "Verify restore receipt",
    )

    positions: list[int] = []
    for step in ordered_steps:
        position = workflow.find(step)
        if position == -1:
            errors.append(
                f"archive restore workflow missing ordered step {step}"
            )
        else:
            positions.append(position)

    if (
        len(positions) == len(ordered_steps)
        and positions != sorted(positions)
    ):
        errors.append(
            "archive restore workflow does not verify before extraction "
            "and evidence validation"
        )

    archive_verify = workflow.find(
        "Verify downloaded archive bundle"
    )
    extract_step = workflow.find("Extract verified archive")

    if (
        archive_verify != -1
        and extract_step != -1
        and archive_verify > extract_step
    ):
        errors.append(
            "archive restore workflow extracts before archive verification"
        )

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
            errors.append(f"archive restore workflow contains forbidden pattern {fragment}")

    return tuple(errors)


def verify_receipt(path: Path) -> tuple[str, ...]:
    errors: list[str] = []

    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load archive restore receipt: {exc}",)

    if not isinstance(receipt, dict):
        return ("archive restore receipt must be an object",)

    required = (
        "schema_version",
        "restored_at",
        "provider",
        "repository",
        "tag",
        "retention_class",
        "restore_run_id",
        "bucket",
        "key_prefix",
        "archive_name",
        "archive_sha256",
        "remote_sha256",
        "downloaded_sha256",
        "remote_verified",
        "download_verified",
        "safe_extract",
        "evidence_path",
    )
    for field in required:
        if field not in receipt:
            errors.append(f"archive restore receipt missing field {field}")

    if receipt.get("schema_version") != 1:
        errors.append("archive restore receipt schema version must be 1")
    if receipt.get("provider") != "aws-s3":
        errors.append("archive restore provider must be aws-s3")
    if receipt.get("retention_class") not in {"operational", "long-term"}:
        errors.append("archive restore retention class is invalid")
    if receipt.get("remote_verified") is not True:
        errors.append("archive restore remote verification did not succeed")
    if receipt.get("download_verified") is not True:
        errors.append("archive restore download verification did not succeed")
    if receipt.get("safe_extract") is not True:
        errors.append("archive restore safe extraction did not succeed")
    if receipt.get("remote_sha256") != receipt.get("archive_sha256"):
        errors.append("remote SHA-256 does not match archive SHA-256")
    if receipt.get("downloaded_sha256") != receipt.get("archive_sha256"):
        errors.append("downloaded SHA-256 does not match archive SHA-256")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())
    if args.receipt is not None:
        errors.extend(verify_receipt(args.receipt))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.receipt is None:
        print("archive restore and disaster recovery policy verified")
    else:
        print(f"archive restore receipt verified: {args.receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
