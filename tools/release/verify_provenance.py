"""Verify Orion release provenance and attestation configuration."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []
    workflow = (root / ".github" / "workflows" / "orion-release.yml").read_text(encoding="utf-8")

    required = (
        "id-token: write",
        "attestations: write",
        "artifact-metadata: write",
        "actions/attest@v4",
        "dist/*.whl",
        "dist/*.tar.gz",
        "dist/SHA256SUMS",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"release provenance configuration missing {fragment}")

    attest_index = workflow.find("actions/attest@v4")
    release_index = workflow.find("Create GitHub Release")
    if attest_index == -1 or release_index == -1 or attest_index > release_index:
        errors.append("release artifacts must be attested before GitHub Release publication")

    candidate = (root / ".github" / "workflows" / "orion-release-candidate.yml").read_text(
        encoding="utf-8"
    )
    if "actions/attest@v4" in candidate:
        errors.append("release-candidate workflow must not publish production attestations")

    return tuple(errors)


def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("release provenance and attestation configuration verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
