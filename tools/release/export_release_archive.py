"""Export a verified MusicClean release archive to durable S3 storage."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _run(*args: str) -> str:
    completed = subprocess.run(
        list(args),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _load_manifest(archive_dir: Path) -> dict[str, Any]:
    path = archive_dir / "release-archive-manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("release archive manifest must be an object")
    return data


def export(archive_dir: Path) -> dict[str, Any]:
    manifest = _load_manifest(archive_dir)
    tag = os.environ["ARCHIVE_TAG"]
    retention_class = os.environ["ARCHIVE_RETENTION_CLASS"]

    if manifest.get("tag") != tag:
        raise ValueError("export tag does not match release archive manifest")
    if manifest.get("retention_class") != retention_class:
        raise ValueError("export retention class does not match release archive manifest")

    bucket = os.environ["ARCHIVE_BUCKET"].strip()
    if not bucket:
        raise ValueError("ARCHIVE_BUCKET is required")

    prefix = os.environ.get("ARCHIVE_PREFIX", "").strip() or "musicclean/releases"
    prefix = prefix.strip("/")

    archive_name = manifest.get("archive_name")
    archive_sha256 = manifest.get("archive_sha256")
    if not isinstance(archive_name, str) or not isinstance(archive_sha256, str):
        raise ValueError("archive manifest is missing archive identity")

    bundle_files = (
        archive_name,
        "release-archive-manifest.json",
        "release-archive.SHA256SUMS",
    )
    key_root = f"{prefix}/{tag}/{retention_class}"

    for name in bundle_files:
        source = archive_dir / name
        if not source.is_file():
            raise ValueError(f"archive bundle file is missing: {name}")

        key = f"{key_root}/{name}"
        command = [
            "aws",
            "s3api",
            "put-object",
            "--bucket",
            bucket,
            "--key",
            key,
            "--body",
            str(source),
        ]
        if name == archive_name:
            command.extend(["--metadata", f"sha256={archive_sha256}"])
        _run(*command)

    remote = json.loads(
        _run(
            "aws",
            "s3api",
            "head-object",
            "--bucket",
            bucket,
            "--key",
            f"{key_root}/{archive_name}",
        )
    )
    if not isinstance(remote, dict):
        raise ValueError("remote archive metadata must be an object")

    metadata = remote.get("Metadata")
    remote_sha256 = metadata.get("sha256") if isinstance(metadata, dict) else None
    if remote_sha256 != archive_sha256:
        raise ValueError("remote archive SHA-256 metadata does not match local archive")

    return {
        "schema_version": 1,
        "exported_at": datetime.now(UTC).isoformat(),
        "provider": "aws-s3",
        "repository": os.environ["ARCHIVE_REPOSITORY"],
        "tag": tag,
        "retention_class": retention_class,
        "source_archive_run_id": int(os.environ["ARCHIVE_SOURCE_RUN_ID"]),
        "export_run_id": int(os.environ["ARCHIVE_EXPORT_RUN_ID"]),
        "bucket": bucket,
        "key_prefix": key_root,
        "archive_name": archive_name,
        "archive_sha256": archive_sha256,
        "remote_sha256": remote_sha256,
        "remote_verified": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    receipt = export(args.archive_dir)
    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
