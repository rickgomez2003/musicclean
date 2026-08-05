from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

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


durable = _load(
    "musicclean_durable_archive_export",
    "tools/release/verify_durable_archive_export.py",
)


def test_repository_durable_export_configuration() -> None:
    assert durable.verify_configuration(ROOT) == ()


def test_valid_export_receipt(tmp_path: Path) -> None:
    receipt = {
        "schema_version": 1,
        "exported_at": "2026-08-05T00:00:00+00:00",
        "provider": "aws-s3",
        "repository": "owner/repo",
        "tag": "v0.6.42",
        "retention_class": "long-term",
        "source_archive_run_id": 10,
        "export_run_id": 11,
        "bucket": "archive-bucket",
        "key_prefix": "musicclean/releases/v0.6.42/long-term",
        "archive_name": "musicclean-v0.6.42-release-evidence.zip",
        "archive_sha256": "abc123",
        "remote_sha256": "abc123",
        "remote_verified": True,
    }
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    assert durable.verify_receipt(path) == ()


def test_mismatched_remote_digest_is_rejected(tmp_path: Path) -> None:
    receipt = {
        "schema_version": 1,
        "exported_at": "2026-08-05T00:00:00+00:00",
        "provider": "aws-s3",
        "repository": "owner/repo",
        "tag": "v0.6.42",
        "retention_class": "long-term",
        "source_archive_run_id": 10,
        "export_run_id": 11,
        "bucket": "archive-bucket",
        "key_prefix": "musicclean/releases/v0.6.42/long-term",
        "archive_name": "musicclean-v0.6.42-release-evidence.zip",
        "archive_sha256": "abc123",
        "remote_sha256": "def456",
        "remote_verified": True,
    }
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    errors = durable.verify_receipt(path)
    assert "durable export remote SHA-256 does not match archive SHA-256" in errors
