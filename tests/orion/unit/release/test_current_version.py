from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from musicclean import __version__

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


current_version = _load(
    "musicclean_current_version",
    "tools/release/current_version.py",
)


def test_github_output_uses_authoritative_version(tmp_path: Path) -> None:
    output = tmp_path / "github-output"

    current_version.write_github_output(output, __version__)

    assert output.read_text(encoding="utf-8") == (
        f"version={__version__}\n"
    )
