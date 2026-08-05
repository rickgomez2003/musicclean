"""Restore and verify a MusicClean release archive from durable S3 storage."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _run(*args: str) -> str:
    completed = subprocess.run(
        list(args),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _safe_extract(archive_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()

    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if root != target and root not in target.parents:
                raise ValueError(f"archive member escapes restore directory: {member.filename}")
        archive.extractall(destination)


def restore(download_dir: Path, extract_dir: Path) -> dict[str, Any]:
    bucket = os.environ["ARCHIVE_BUCKET"].strip()
    if not bucket:
        raise ValueError("ARCHIVE_BUCKET is required")

    tag = os.environ["ARCHIVE_TAG"]
    retention_class = os.environ["ARCHIVE_RETENTION_CLASS"]
    prefix = os.environ.get("ARCHIVE_PREFIX", "").strip() or "musicclean/releases"
    prefix = prefix.strip("/")
    key_root = f"{prefix}/{tag}/{retention_class}"

    download_dir.mkdir(parents=True, exist_ok=True)

    manifest_key = f"{key_root}/release-archive-manifest.json"
    sums_key = f"{key_root}/release-archive.SHA256SUMS"

    _run(
        "aws",
        "s3api",
        "get-object",
        "--bucket",
        bucket,
        "--key",
        manifest_key,
        str(download_dir / "release-archive-manifest.json"),
    )
    _run(
        "aws",
        "s3api",
        "get-object",
        "--bucket",
        bucket,
        "--key",
        sums_key,
        str(download_dir / "release-archive.SHA256SUMS"),
    )

    manifest = json.loads(
        (download_dir / "release-archive-manifest.json").read_text(encoding="utf-8")
    )
    if not isinstance(manifest, dict):
        raise ValueError("release archive manifest must be an object")

    if manifest.get("tag") != tag:
        raise ValueError("restore tag does not match archive manifest")
    if manifest.get("retention_class") != retention_class:
        raise ValueError("restore retention class does not match archive manifest")

    archive_name = manifest.get("archive_name")
    archive_sha256 = manifest.get("archive_sha256")
    if not isinstance(archive_name, str) or not isinstance(archive_sha256, str):
        raise ValueError("archive manifest is missing archive identity")

    archive_key = f"{key_root}/{archive_name}"
    archive_path = download_dir / archive_name

    remote = json.loads(
        _run(
            "aws",
            "s3api",
            "head-object",
            "--bucket",
            bucket,
            "--key",
            archive_key,
        )
    )
    if not isinstance(remote, dict):
        raise ValueError("remote archive metadata must be an object")
    metadata = remote.get("Metadata")
    remote_sha256 = metadata.get("sha256") if isinstance(metadata, dict) else None
    if remote_sha256 != archive_sha256:
        raise ValueError("remote archive SHA-256 metadata does not match manifest")

    _run(
        "aws",
        "s3api",
        "get-object",
        "--bucket",
        bucket,
        "--key",
        archive_key,
        str(archive_path),
    )

    downloaded_sha256 = sha256(archive_path)
    if downloaded_sha256 != archive_sha256:
        raise ValueError("downloaded archive SHA-256 does not match manifest")

    # Do not extract here.
    #
    # The workflow must independently verify the downloaded archive bundle
    # before any archive member is written to the restore destination.

    return {
        "schema_version": 1,
        "restored_at": datetime.now(UTC).isoformat(),
        "provider": "aws-s3",
        "repository": os.environ["RESTORE_REPOSITORY"],
        "tag": tag,
        "retention_class": retention_class,
        "restore_run_id": int(os.environ["RESTORE_RUN_ID"]),
        "bucket": bucket,
        "key_prefix": key_root,
        "archive_name": archive_name,
        "archive_sha256": archive_sha256,
        "remote_sha256": remote_sha256,
        "downloaded_sha256": downloaded_sha256,
        "remote_verified": True,
        "download_verified": True,
        "safe_extract": False,
        "evidence_path": "restored-evidence/release-audit-evidence.json",
    }


def extract_verified_archive(
    download_dir: Path,
    extract_dir: Path,
    receipt_path: Path,
) -> dict[str, object]:
    """Safely extract an archive after independent bundle verification."""

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not isinstance(receipt, dict):
        raise ValueError("restore receipt must be an object")

    archive_name = receipt.get("archive_name")
    archive_sha256 = receipt.get("archive_sha256")

    if not isinstance(archive_name, str) or not isinstance(archive_sha256, str):
        raise ValueError("restore receipt is missing archive identity")

    archive_path = download_dir / archive_name
    if not archive_path.is_file():
        raise ValueError("verified archive is missing from download directory")

    downloaded_sha256 = sha256(archive_path)
    if downloaded_sha256 != archive_sha256:
        raise ValueError(
            "archive SHA-256 changed after verification and before extraction"
        )

    _safe_extract(archive_path, extract_dir)

    receipt["downloaded_sha256"] = downloaded_sha256
    receipt["safe_extract"] = True

    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-dir", type=Path, required=True)
    parser.add_argument("--extract-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument(
        "--extract-verified",
        action="store_true",
        help="Extract an independently verified downloaded archive.",
    )
    args = parser.parse_args()

    if args.extract_verified:
        receipt = extract_verified_archive(
            args.download_dir,
            args.extract_dir,
            args.receipt,
        )
    else:
        receipt = restore(args.download_dir, args.extract_dir)

    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
