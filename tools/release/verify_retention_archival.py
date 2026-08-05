"""Verify MusicClean release retention and archival policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []
    path = root / "release" / "retention.toml"
    try:
        with path.open("rb") as stream:
            document = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return (f"unable to load release retention policy: {exc}",)

    retention = document.get("retention")
    if not isinstance(retention, dict):
        return ("release retention table is missing",)

    if retention.get("schema_version") != 1:
        errors.append("retention schema version must be 1")
    if retention.get("default_class") != "operational":
        errors.append("default retention class must be operational")
    if retention.get("artifact_retention_days") != 90:
        errors.append("Actions archive retention must be 90 days")
    if retention.get("preserve_source_evidence") is not True:
        errors.append("source evidence preservation must be enabled")
    if retention.get("deterministic_archives") is not True:
        errors.append("deterministic archives must be enabled")
    if retention.get("external_export_required_for_long_term") is not True:
        errors.append("long-term retention must require external export")

    classes = retention.get("classes")
    if not isinstance(classes, dict):
        errors.append("retention classes are missing")
    else:
        operational = classes.get("operational")
        long_term = classes.get("long-term")
        if not isinstance(operational, dict) or operational.get("minimum_days") != 90:
            errors.append("operational retention must be 90 days")
        if not isinstance(long_term, dict) or long_term.get("minimum_days") != 2555:
            errors.append("long-term retention must be 2555 days")

    workflow = (root / ".github" / "workflows" / "orion-release-archive.yml").read_text(
        encoding="utf-8"
    )

    required = (
        "workflow_dispatch:",
        "actions: read",
        "contents: read",
        "gh run download",
        "verify_audit_evidence.py",
        "build_release_archive.py",
        "verify_retention_archival.py",
        "actions/upload-artifact@v4",
        "retention-days: 90",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"release archive workflow missing {fragment}")

    forbidden = (
        "contents: write",
        "gh release edit",
        "gh release create",
        "gh release upload",
        "gh release delete",
        "python -m build",
        "actions/attest",
        "--admin",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"release archive workflow contains forbidden pattern {fragment}")

    return tuple(errors)


def verify_archive(archive_dir: Path) -> tuple[str, ...]:
    errors: list[str] = []
    manifest_path = archive_dir / "release-archive-manifest.json"
    sums_path = archive_dir / "release-archive.SHA256SUMS"

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (f"unable to load release archive manifest: {exc}",)

    if not isinstance(manifest, dict):
        return ("release archive manifest must be an object",)

    required = (
        "schema_version",
        "generated_at",
        "repository",
        "tag",
        "retention_class",
        "source_evidence_run_id",
        "archive_run_id",
        "archive_name",
        "archive_sha256",
        "source_evidence_sha256",
    )
    for field in required:
        if field not in manifest:
            errors.append(f"archive manifest missing field {field}")

    archive_name = manifest.get("archive_name")
    if isinstance(archive_name, str):
        archive_path = archive_dir / archive_name
        if not archive_path.exists():
            errors.append("archive file is missing")
        elif sha256(archive_path) != manifest.get("archive_sha256"):
            errors.append("archive checksum does not match manifest")
    else:
        errors.append("archive_name must be a string")

    if not sums_path.exists():
        errors.append("release archive checksum file is missing")

    if manifest.get("retention_class") not in {"operational", "long-term"}:
        errors.append("archive retention class is invalid")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-dir", type=Path)
    args = parser.parse_args()

    errors = list(verify_configuration())
    if args.archive_dir is not None:
        errors.extend(verify_archive(args.archive_dir))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.archive_dir is None:
        print("release retention and archival policy verified")
    else:
        print(f"release archive verified: {args.archive_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
