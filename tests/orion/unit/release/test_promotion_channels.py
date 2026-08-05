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


promotion = _load(
    "musicclean_release_promotion",
    "tools/release/verify_promotion_channels.py",
)


def test_repository_release_promotion_configuration() -> None:
    assert promotion.verify_configuration(ROOT) == ()


def test_unknown_channel_is_rejected_without_github_lookup() -> None:
    assert promotion.verify_promotion("owner/repo", "v0.6.38", "nightly") == (
        "unsupported release channel: nightly",
    )
