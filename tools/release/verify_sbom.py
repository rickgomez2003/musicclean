"""Verify MusicClean SBOM generation and attestation policy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []
    workflow = (root / ".github" / "workflows" / "orion-release.yml").read_text(encoding="utf-8")

    required = (
        "anchore/sbom-action@v0",
        "format: spdx-json",
        ".sbom.spdx.json",
        "upload-artifact: false",
        "upload-release-assets: false",
        "python tools/release/verify_sbom.py",
        "actions/attest@v4",
        "sbom-path:",
        "dist/*.sbom.spdx.json",
        "python tools/release/checksums.py dist",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"SBOM release configuration missing {fragment}")

    generate_index = workflow.find("Generate SPDX JSON SBOM")
    checksum_index = workflow.find("Generate SHA-256 checksums")
    sbom_attest_index = workflow.find("Attest wheel SBOM")
    release_index = workflow.find("Create GitHub Release")

    if not (-1 < generate_index < checksum_index < sbom_attest_index < release_index):
        errors.append(
            "SBOM generation, checksums, SBOM attestation and release publication "
            "are not in the required order"
        )

    return tuple(errors)


def verify_document(document: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []

    spdx_version = document.get("spdxVersion")
    if not isinstance(spdx_version, str) or not spdx_version.startswith("SPDX-"):
        errors.append("SBOM is not an SPDX document")

    namespace = document.get("documentNamespace")
    if not isinstance(namespace, str) or not namespace.strip():
        errors.append("SBOM documentNamespace is missing")

    packages = document.get("packages")
    if not isinstance(packages, list) or not packages:
        errors.append("SBOM does not contain any packages")

    return tuple(errors)


def verify_file(path: Path) -> tuple[str, ...]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to read SBOM: {exc}",)

    if not isinstance(document, dict):
        return ("SBOM root must be a JSON object",)

    return verify_document(document)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sbom", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())
    if args.sbom is not None:
        errors.extend(verify_file(args.sbom))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.sbom is None:
        print("SBOM generation and attestation configuration verified")
    else:
        print(f"SBOM verified: {args.sbom}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
