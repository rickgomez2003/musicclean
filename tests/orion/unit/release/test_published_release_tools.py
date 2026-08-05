from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[4]


def _load(name: str, rel: str) -> ModuleType:
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load release tool: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


published = _load(
    "musicclean_published_release",
    "tools/release/verify_published_release.py",
)


def test_expected_release_asset_names() -> None:
    assert published.expected_asset_names("0.6.30") == (
        "musicclean-0.6.30-py3-none-any.whl",
        "musicclean-0.6.30.tar.gz",
    )


def test_downloaded_release_requires_all_assets(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="missing published release assets"):
        published.discover_downloaded_release(tmp_path, tag="v0.6.30")


def test_release_checksums_verify_downloaded_artifacts(tmp_path: Path) -> None:
    wheel = tmp_path / "musicclean-0.6.30-py3-none-any.whl"
    sdist = tmp_path / "musicclean-0.6.30.tar.gz"
    sums = tmp_path / "SHA256SUMS"
    wheel.write_bytes(b"wheel")
    sdist.write_bytes(b"sdist")
    sums.write_text(
        f"{published.sha256(wheel)}  {wheel.name}\n{published.sha256(sdist)}  {sdist.name}\n",
        encoding="utf-8",
    )
    release = published.discover_downloaded_release(tmp_path, tag="v0.6.30")
    assert published.verify_checksums(release) == ()
