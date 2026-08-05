from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[4]


def _load(name: str, relative: str) -> ModuleType:
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load release tool: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


restore = _load(
    "musicclean_archive_restore",
    "tools/release/verify_archive_restore.py",
)
restore_impl = _load(
    "musicclean_archive_restore_impl",
    "tools/release/restore_release_archive.py",
)


def test_repository_archive_restore_configuration() -> None:
    assert restore.verify_configuration(ROOT) == ()


def test_valid_restore_receipt(tmp_path: Path) -> None:
    receipt = {
        "schema_version": 1,
        "restored_at": "2026-08-05T00:00:00+00:00",
        "provider": "aws-s3",
        "repository": "owner/repo",
        "tag": "v0.6.43",
        "retention_class": "long-term",
        "restore_run_id": 20,
        "bucket": "archive-bucket",
        "key_prefix": "musicclean/releases/v0.6.43/long-term",
        "archive_name": "musicclean-v0.6.43-release-evidence.zip",
        "archive_sha256": "abc123",
        "remote_sha256": "abc123",
        "downloaded_sha256": "abc123",
        "remote_verified": True,
        "download_verified": True,
        "safe_extract": True,
        "evidence_path": "restored-evidence/release-audit-evidence.json",
    }
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    assert restore.verify_receipt(path) == ()


def test_safe_extract_rejects_path_traversal(tmp_path: Path) -> None:
    archive_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../escape.txt", b"bad")

    with pytest.raises(ValueError, match="escapes restore directory"):
        restore_impl._safe_extract(archive_path, tmp_path / "out")

def _write_restore_receipt(
    path: Path,
    archive_path: Path,
    *,
    safe_extract: bool = False,
) -> None:
    digest = restore_impl.sha256(archive_path)
    receipt = {
        "schema_version": 1,
        "restored_at": "2026-08-05T00:00:00+00:00",
        "provider": "aws-s3",
        "repository": "owner/repo",
        "tag": "v0.6.43",
        "retention_class": "long-term",
        "restore_run_id": 20,
        "bucket": "archive-bucket",
        "key_prefix": "musicclean/releases/v0.6.43/long-term",
        "archive_name": archive_path.name,
        "archive_sha256": digest,
        "remote_sha256": digest,
        "downloaded_sha256": digest,
        "remote_verified": True,
        "download_verified": True,
        "safe_extract": safe_extract,
        "evidence_path": (
            "restored-evidence/release-audit-evidence.json"
        ),
    }
    path.write_text(json.dumps(receipt), encoding="utf-8")


def test_verified_extraction_rehashes_archive_before_extracting(
    tmp_path: Path,
) -> None:
    download_dir = tmp_path / "download"
    extract_dir = tmp_path / "extract"
    download_dir.mkdir()

    archive_path = download_dir / "release-evidence.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "release-audit-evidence.json",
            b'{"verified": true}',
        )

    receipt_path = tmp_path / "receipt.json"
    _write_restore_receipt(receipt_path, archive_path)

    receipt = restore_impl.extract_verified_archive(
        download_dir,
        extract_dir,
        receipt_path,
    )

    assert receipt["safe_extract"] is True
    assert receipt["downloaded_sha256"] == receipt["archive_sha256"]
    assert (
        extract_dir / "release-audit-evidence.json"
    ).is_file()


def test_verified_extraction_rejects_archive_changed_after_verification(
    tmp_path: Path,
) -> None:
    download_dir = tmp_path / "download"
    extract_dir = tmp_path / "extract"
    download_dir.mkdir()

    archive_path = download_dir / "release-evidence.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "release-audit-evidence.json",
            b'{"verified": true}',
        )

    receipt_path = tmp_path / "receipt.json"
    _write_restore_receipt(receipt_path, archive_path)

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "release-audit-evidence.json",
            b'{"tampered": true}',
        )

    with pytest.raises(
        ValueError,
        match=(
            "archive SHA-256 changed after verification "
            "and before extraction"
        ),
    ):
        restore_impl.extract_verified_archive(
            download_dir,
            extract_dir,
            receipt_path,
        )

    assert not extract_dir.exists()


def test_verified_extraction_still_rejects_path_traversal(
    tmp_path: Path,
) -> None:
    download_dir = tmp_path / "download"
    extract_dir = tmp_path / "extract"
    download_dir.mkdir()

    archive_path = download_dir / "release-evidence.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../escape.txt", b"bad")

    receipt_path = tmp_path / "receipt.json"
    _write_restore_receipt(receipt_path, archive_path)

    with pytest.raises(
        ValueError,
        match="escapes restore directory",
    ):
        restore_impl.extract_verified_archive(
            download_dir,
            extract_dir,
            receipt_path,
        )

    assert not (tmp_path / "escape.txt").exists()
