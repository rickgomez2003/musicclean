from __future__ import annotations

import importlib.util
import sys
import zipfile
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
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


candidate = _load_tool(
    "musicclean_release_candidate",
    "tools/release/validate_candidate.py",
)


def test_discover_artifacts_requires_single_versioned_pair(tmp_path: Path) -> None:
    wheel = tmp_path / "musicclean-0.6.29-py3-none-any.whl"
    sdist = tmp_path / "musicclean-0.6.29.tar.gz"
    checksums = tmp_path / "SHA256SUMS"

    wheel.write_bytes(b"wheel")
    sdist.write_bytes(b"sdist")
    checksums.write_text(
        f"abc  {wheel.name}\ndef  {sdist.name}\n",
        encoding="utf-8",
    )

    artifacts = candidate.discover_artifacts(tmp_path, "0.6.29")

    assert artifacts.wheel == wheel
    assert artifacts.sdist == sdist
    assert artifacts.checksums == checksums


def test_discover_artifacts_rejects_wrong_version(tmp_path: Path) -> None:
    (tmp_path / "musicclean-0.6.28-py3-none-any.whl").write_bytes(b"wheel")
    (tmp_path / "musicclean-0.6.28.tar.gz").write_bytes(b"sdist")
    (tmp_path / "SHA256SUMS").write_text("placeholder\n", encoding="utf-8")

    with pytest.raises(ValueError, match="wheel version"):
        candidate.discover_artifacts(tmp_path, "0.6.29")


def test_wheel_metadata_version_is_read_from_built_artifact(
    tmp_path: Path,
) -> None:
    wheel = tmp_path / "musicclean-0.6.29-py3-none-any.whl"

    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "musicclean-0.6.29.dist-info/METADATA",
            "Metadata-Version: 2.4\nName: musicclean\nVersion: 0.6.29\n",
        )

    assert candidate.wheel_metadata_version(wheel) == "0.6.29"
