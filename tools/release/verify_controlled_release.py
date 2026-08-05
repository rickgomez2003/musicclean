"""Verify repository readiness for a controlled release."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from musicclean import __version__

ROOT = Path(__file__).resolve().parents[2]


def _read(root: Path, path: str) -> str:
    return (root / path).read_text(encoding="utf-8")


def _candidate_workflow_is_version_driven(text: str) -> bool:
    required = (
        "tools/release/current_version.py",
        "steps.version.outputs.version",
        'verify_version.py --expected "$RELEASE_VERSION"',
        'verify_controlled_release.py --expected "$RELEASE_VERSION"',
        'validate_candidate.py --dist dist --expected "$RELEASE_VERSION"',
    )
    return all(item in text for item in required)


def verify(
    expected: str,
    *,
    package_version: str = __version__,
    root: Path = ROOT,
) -> tuple[str, ...]:
    errors: list[str] = []

    if package_version != expected:
        errors.append(f"package version mismatch: package={package_version} expected={expected}")

    candidate = _read(root, ".github/workflows/orion-release-candidate.yml")
    if not _candidate_workflow_is_version_driven(candidate):
        errors.append(
            "release-candidate workflow does not derive its version "
            "from the authoritative package version"
        )

    release = _read(root, ".github/workflows/orion-release.yml")
    if 'tags:\n      - "v*.*.*"' not in release:
        errors.append("release workflow is not restricted to semantic version tags")

    process = _read(root, "docs/releases/RELEASE-PROCESS.md")
    normalized = process.lower().replace("-", " ")
    if "annotated tag" not in normalized:
        errors.append("release process does not require an annotated tag")
    if "release candidate" not in normalized:
        errors.append("release process does not require release-candidate validation")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected", required=True)
    args = parser.parse_args()
    errors = verify(args.expected)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"controlled release {args.expected} is ready for PR validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
