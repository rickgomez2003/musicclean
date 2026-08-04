"""Verify repository readiness for a controlled release."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from musicclean import __version__

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _candidate_workflow_version(text: str) -> str | None:
    match = re.search(
        r"verify_version\.py --expected (\d+\.\d+\.\d+)",
        text,
    )
    return match.group(1) if match else None


def verify(expected: str) -> tuple[str, ...]:
    errors: list[str] = []

    if __version__ != expected:
        errors.append(f"package version mismatch: package={__version__} expected={expected}")

    candidate = _read(".github/workflows/orion-release-candidate.yml")
    candidate_version = _candidate_workflow_version(candidate)
    if candidate_version != expected:
        errors.append("release-candidate workflow version does not match expected release")

    release = _read(".github/workflows/orion-release.yml")
    if 'tags:\n      - "v*.*.*"' not in release:
        errors.append("release workflow is not restricted to semantic version tags")

    process = _read("docs/releases/RELEASE-PROCESS.md")
    if "annotated tag" not in process.lower():
        errors.append("release process does not require an annotated tag")
    if "release candidate" not in process.lower():
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
