from __future__ import annotations

import importlib.util
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


rollback = _load(
    "musicclean_release_rollback",
    "tools/release/verify_rollback_recovery.py",
)


def test_repository_rollback_configuration() -> None:
    assert rollback.verify_configuration(ROOT) == ()


def test_same_current_and_recovery_tag_is_rejected_without_github_lookup() -> None:
    assert rollback.verify_request("owner/repo", "v0.6.38", "v0.6.38") == (
        "current and recovery tags must be different",
    )
