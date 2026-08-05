"""Verify MusicClean durable archive export policy and receipts."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    path = root / "release" / "durable-export.toml"
    try:
        with path.open("rb") as stream:
            document = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return (f"unable to load durable export policy: {exc}",)

    export = document.get("export")
    if not isinstance(export, dict):
        return ("durable export policy table is missing",)

    expected = {
        "schema_version": 1,
        "provider": "aws-s3",
        "environment": "release-archive-export",
        "authentication": "github-oidc",
        "default_prefix": "musicclean/releases",
        "verify_local_archive": True,
        "write_sha256_metadata": True,
        "verify_remote_sha256_metadata": True,
        "upload_receipt": True,
        "preserve_github_release": True,
        "preserve_archive_bundle": True,
    }
    if export != expected:
        errors.append("durable export policy does not match expected safe values")

    workflow = (root / ".github" / "workflows" / "orion-durable-archive-export.yml").read_text(
        encoding="utf-8"
    )

    required = (
        "workflow_dispatch:",
        "actions: read",
        "contents: read",
        "id-token: write",
        "name: release-archive-export",
        "gh run download",
        "verify_retention_archival.py",
        "aws-actions/configure-aws-credentials@v5",
        "role-to-assume: ${{ secrets.AWS_ARCHIVE_ROLE_ARN }}",
        "export_release_archive.py",
        "verify_durable_archive_export.py",
        "actions/upload-artifact@v4",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"durable export workflow missing {fragment}")

    forbidden = (
        "contents: write",
        "gh release edit",
        "gh release create",
        "gh release upload",
        "gh release delete",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "--admin",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"durable export workflow contains forbidden pattern {fragment}")

    return tuple(errors)


def verify_receipt(path: Path) -> tuple[str, ...]:
    errors: list[str] = []

    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load durable export receipt: {exc}",)

    if not isinstance(receipt, dict):
        return ("durable export receipt must be an object",)

    required = (
        "schema_version",
        "exported_at",
        "provider",
        "repository",
        "tag",
        "retention_class",
        "source_archive_run_id",
        "export_run_id",
        "bucket",
        "key_prefix",
        "archive_name",
        "archive_sha256",
        "remote_sha256",
        "remote_verified",
    )
    for field in required:
        if field not in receipt:
            errors.append(f"durable export receipt missing field {field}")

    if receipt.get("schema_version") != 1:
        errors.append("durable export receipt schema version must be 1")
    if receipt.get("provider") != "aws-s3":
        errors.append("durable export provider must be aws-s3")
    if receipt.get("retention_class") not in {"operational", "long-term"}:
        errors.append("durable export retention class is invalid")
    if receipt.get("remote_verified") is not True:
        errors.append("durable export remote verification did not succeed")
    if receipt.get("remote_sha256") != receipt.get("archive_sha256"):
        errors.append("durable export remote SHA-256 does not match archive SHA-256")

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
        print("durable archive export policy verified")
    else:
        print(f"durable archive export receipt verified: {args.receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
