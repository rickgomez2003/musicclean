from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

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


controlled_release = _load_tool(
    "musicclean_controlled_release",
    "tools/release/verify_controlled_release.py",
)


def test_controlled_release_repository_is_aligned_to_0_6_30() -> None:
    assert controlled_release.verify("0.6.30") == ()


def test_controlled_release_rejects_wrong_expected_version() -> None:
    errors = controlled_release.verify("0.6.29")
    assert any("package version mismatch" in error for error in errors)
