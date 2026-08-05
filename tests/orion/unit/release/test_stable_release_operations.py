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


stable_operations = _load(
    "musicclean_stable_release_operations",
    "tools/release/verify_stable_operations.py",
)


def test_repository_stable_release_invariants() -> None:
    assert stable_operations.verify(ROOT) == ()
