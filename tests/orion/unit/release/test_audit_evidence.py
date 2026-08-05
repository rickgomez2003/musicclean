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


audit = _load(
    "musicclean_release_audit_evidence",
    "tools/release/verify_audit_evidence.py",
)


def test_repository_audit_evidence_configuration() -> None:
    assert audit.verify_configuration(ROOT) == ()


def test_valid_evidence_document(tmp_path: Path) -> None:
    evidence = {
        "schema_version": 1,
        "generated_at": "2026-08-05T00:00:00+00:00",
        "repository": "owner/repo",
        "tag": "v0.6.40",
        "source_tag": "v0.6.40",
        "tag_commit": "abc123",
        "head_commit": "abc123",
        "actor": "maintainer",
        "workflow": "Orion Release Audit Evidence",
        "run_id": 1,
        "run_attempt": 1,
        "run_url": "https://github.com/owner/repo/actions/runs/1",
        "release": {
            "tagName": "v0.6.40",
            "isDraft": False,
            "isPrerelease": False,
        },
        "assets": [],
        "checksum_errors": [],
        "has_sha256sums": True,
        "has_sbom": True,
        "has_wheel": True,
        "has_sdist": True,
    }
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    assert audit.verify_evidence(path) == ()


def test_source_tag_must_match_requested_tag(tmp_path: Path) -> None:
    evidence = {
        "schema_version": 1,
        "generated_at": "2026-08-05T00:00:00+00:00",
        "repository": "owner/repo",
        "tag": "v0.6.40",
        "source_tag": "v0.6.39",
        "tag_commit": "abc123",
        "head_commit": "abc123",
        "actor": "maintainer",
        "workflow": "Orion Release Audit Evidence",
        "run_id": 1,
        "run_attempt": 1,
        "run_url": "https://github.com/owner/repo/actions/runs/1",
        "release": {"tagName": "v0.6.40", "isDraft": False},
        "assets": [],
        "checksum_errors": [],
        "has_sha256sums": True,
        "has_sbom": True,
        "has_wheel": True,
        "has_sdist": True,
    }
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")
    errors = audit.verify_evidence(path)
    assert "checked-out source tag does not match requested release tag" in errors
