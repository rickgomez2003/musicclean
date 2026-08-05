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


archive = _load(
    "musicclean_release_retention_archival",
    "tools/release/verify_retention_archival.py",
)


def test_repository_retention_archival_configuration() -> None:
    assert archive.verify_configuration(ROOT) == ()


def test_invalid_retention_class_is_rejected(tmp_path: Path) -> None:
    archive_file = tmp_path / "release.zip"
    archive_file.write_bytes(b"archive")
    manifest = {
        "schema_version": 1,
        "generated_at": "2026-08-05T00:00:00+00:00",
        "repository": "owner/repo",
        "tag": "v0.6.41",
        "retention_class": "forever",
        "source_evidence_run_id": 1,
        "archive_run_id": 2,
        "archive_name": archive_file.name,
        "archive_sha256": archive.sha256(archive_file),
        "source_evidence_sha256": "abc123",
    }
    (tmp_path / "release-archive-manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    (tmp_path / "release-archive.SHA256SUMS").write_text(
        f"{archive.sha256(archive_file)}  {archive_file.name}\n",
        encoding="utf-8",
    )
    errors = archive.verify_archive(tmp_path)
    assert "archive retention class is invalid" in errors
