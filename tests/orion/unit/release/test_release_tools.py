"""Tests for repository release tooling."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


def _load_tool(name: str, relative_path: str) -> ModuleType:
    path = REPOSITORY_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)

    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load release tool: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checksums = _load_tool(
    "musicclean_release_checksums",
    "tools/release/checksums.py",
)
verify_version = _load_tool(
    "musicclean_release_verify_version",
    "tools/release/verify_version.py",
)


def test_release_tag_normalization() -> None:
    assert verify_version.normalize_tag("v0.6.28") == "0.6.28"
    assert verify_version.normalize_tag("0.6.28") == "0.6.28"


def test_invalid_release_tag_is_rejected() -> None:
    with pytest.raises(ValueError):
        verify_version.normalize_tag("release-0.6.28")


def test_checksum_is_stable(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.whl"
    artifact.write_bytes(b"musicclean")

    assert checksums.sha256(artifact) == (
        "0185f52d8f11a116ce59adb063e723f377dedec445c613f5b7891883b6692c7c"
    )
