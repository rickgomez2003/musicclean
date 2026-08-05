"""Verify stable release operational invariants."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from musicclean import __version__

ROOT = Path(__file__).resolve().parents[2]

SEMVER_LITERAL = re.compile(r"\b0\.6\.\d+\b")
PACKAGE_VERSION = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)$"
)


def verify(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    candidate = (root / ".github" / "workflows" / "orion-release-candidate.yml").read_text(
        encoding="utf-8"
    )

    if SEMVER_LITERAL.search(candidate):
        errors.append("release-candidate workflow contains a hard-coded MusicClean version")

    for fragment in (
        "tools/release/current_version.py",
        "steps.version.outputs.version",
        "RELEASE_VERSION",
    ):
        if fragment not in candidate:
            errors.append(f"release-candidate workflow missing {fragment}")

    workflows = root / ".github" / "workflows"

    for path in sorted(workflows.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")

        if "actions/checkout@v4" in text or "actions/checkout@v5" in text:
            errors.append(f"{path.name} uses an obsolete checkout action major")

        if "actions/setup-python@v5" in text:
            errors.append(f"{path.name} uses an obsolete setup-python action major")

    if PACKAGE_VERSION.fullmatch(__version__) is None:
        errors.append(f"authoritative package version is not semantic: {__version__}")

    return tuple(errors)


def main() -> int:
    errors = verify()

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("stable release operational invariants verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
