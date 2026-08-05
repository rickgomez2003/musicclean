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


def _create_release_repository(root: Path) -> None:
    candidate = root / ".github" / "workflows" / "orion-release-candidate.yml"
    release = root / ".github" / "workflows" / "orion-release.yml"
    process = root / "docs" / "releases" / "RELEASE-PROCESS.md"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    process.parent.mkdir(parents=True, exist_ok=True)

    candidate.write_text(
        """
id: version
run: python tools/release/current_version.py
version: ${{ steps.version.outputs.version }}
verify: python tools/release/verify_version.py --expected "$RELEASE_VERSION"
ready: python tools/release/verify_controlled_release.py --expected "$RELEASE_VERSION"
artifact: python tools/release/validate_candidate.py --dist dist --expected "$RELEASE_VERSION"
""".lstrip(),
        encoding="utf-8",
    )
    release.write_text(
        'on:\n  push:\n    tags:\n      - "v*.*.*"\n',
        encoding="utf-8",
    )
    process.write_text(
        "A release candidate must pass. Create an annotated tag only from the validated commit.\n",
        encoding="utf-8",
    )


def test_controlled_release_accepts_version_driven_repository(tmp_path: Path) -> None:
    _create_release_repository(tmp_path)
    assert (
        controlled_release.verify(
            "1.2.3",
            package_version="1.2.3",
            root=tmp_path,
        )
        == ()
    )


def test_controlled_release_rejects_wrong_package_version(tmp_path: Path) -> None:
    _create_release_repository(tmp_path)
    errors = controlled_release.verify(
        "1.2.3",
        package_version="1.2.4",
        root=tmp_path,
    )
    assert any("package version mismatch" in error for error in errors)
