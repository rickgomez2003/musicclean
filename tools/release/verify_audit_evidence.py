"""Verify MusicClean release audit evidence policy and evidence files."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []
    policy_path = root / "release" / "audit-evidence.toml"

    try:
        with policy_path.open("rb") as stream:
            document = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return (f"unable to load audit evidence policy: {exc}",)

    evidence = document.get("evidence")
    if not isinstance(evidence, dict):
        return ("audit evidence policy table is missing",)

    expected = {
        "schema_version": 1,
        "workflow": "Orion Release Audit Evidence",
        "retention_days": 90,
        "require_release_metadata": True,
        "require_sha256sums": True,
        "require_sbom": True,
        "require_wheel": True,
        "require_sdist": True,
        "preserve_release": True,
        "read_only_release_access": True,
    }
    if evidence != expected:
        errors.append("audit evidence policy does not match expected safe values")

    workflow = (
        root / ".github" / "workflows" / "orion-release-audit-evidence.yml"
    ).read_text(encoding="utf-8")

    required = (
        "workflow_dispatch:",
        "contents: read",
        "gh release view",
        "gh release download",
        "ref: ${{ inputs.tag }}",
        "path: audited-source",
        "--source audited-source",
        "build_audit_evidence.py",
        "verify_audit_evidence.py",
        "actions/upload-artifact@v4",
        "retention-days: 90",
        "fetch-depth: 0",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"audit evidence workflow missing {fragment}")

    forbidden = (
        "contents: write",
        "gh release edit",
        "gh release create",
        "gh release delete",
        "gh release upload",
        "python -m build",
        "actions/attest",
        "--admin",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"audit evidence workflow contains forbidden pattern {fragment}")

    return tuple(errors)


def verify_evidence(path: Path) -> tuple[str, ...]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load audit evidence: {exc}",)

    if not isinstance(data, dict):
        return ("audit evidence root must be a JSON object",)

    required_fields = (
        "schema_version",
        "generated_at",
        "repository",
        "tag",
        "source_tag",
        "tag_commit",
        "head_commit",
        "actor",
        "workflow",
        "run_id",
        "run_attempt",
        "run_url",
        "release",
        "assets",
        "checksum_errors",
        "has_sha256sums",
        "has_sbom",
        "has_wheel",
        "has_sdist",
    )
    for field in required_fields:
        if field not in data:
            errors.append(f"audit evidence missing field {field}")

    if data.get("schema_version") != 1:
        errors.append("audit evidence schema version must be 1")
    if data.get("source_tag") != data.get("tag"):
        errors.append("checked-out source tag does not match requested release tag")
    if data.get("tag_commit") != data.get("head_commit"):
        errors.append("checked-out commit does not match release tag commit")
    if data.get("checksum_errors") != []:
        errors.append("published release checksum verification failed")
    if data.get("has_sha256sums") is not True:
        errors.append("published release is missing SHA256SUMS")
    if data.get("has_sbom") is not True:
        errors.append("published release is missing SPDX SBOM")
    if data.get("has_wheel") is not True:
        errors.append("published release is missing wheel")
    if data.get("has_sdist") is not True:
        errors.append("published release is missing source distribution")

    release = data.get("release")
    if not isinstance(release, dict):
        errors.append("release metadata must be an object")
    else:
        if release.get("isDraft") is True:
            errors.append("draft releases cannot produce final audit evidence")
        if release.get("tagName") != data.get("tag"):
            errors.append("release metadata tag does not match requested tag")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())
    if args.evidence is not None:
        errors.extend(verify_evidence(args.evidence))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.evidence is None:
        print("release audit trail and evidence policy verified")
    else:
        print(f"release audit evidence verified: {args.evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
