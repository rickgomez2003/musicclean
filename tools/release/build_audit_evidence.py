"""Build a machine-readable evidence record for an existing MusicClean release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(source: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def parse_sha256sums(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        digest, name = line.split(maxsplit=1)
        result[name.lstrip("*")] = digest
    return result


def build(
    release_metadata: Path,
    assets_dir: Path,
    source_dir: Path,
) -> dict[str, Any]:
    release = json.loads(release_metadata.read_text(encoding="utf-8"))
    if not isinstance(release, dict):
        raise ValueError("release metadata must be a JSON object")

    assets = sorted(path for path in assets_dir.iterdir() if path.is_file())
    checksums_path = assets_dir / "SHA256SUMS"
    declared = parse_sha256sums(checksums_path) if checksums_path.exists() else {}

    asset_records: list[dict[str, Any]] = []
    checksum_errors: list[str] = []
    asset_names = {path.name for path in assets}

    for path in assets:
        digest = sha256(path)
        declared_digest = declared.get(path.name)
        verified = declared_digest == digest if declared_digest is not None else None

        if path.name != "SHA256SUMS" and declared_digest is None:
            checksum_errors.append(f"missing-checksum:{path.name}")
        elif verified is False:
            checksum_errors.append(f"checksum-mismatch:{path.name}")

        asset_records.append(
            {
                "name": path.name,
                "size": path.stat().st_size,
                "sha256": digest,
                "declared_sha256": declared_digest,
                "checksum_verified": verified,
            }
        )

    for declared_name in sorted(set(declared) - asset_names):
        checksum_errors.append(f"missing-asset:{declared_name}")

    tag = os.environ["EVIDENCE_TAG"]
    repository = os.environ["EVIDENCE_REPOSITORY"]
    server_url = os.environ["EVIDENCE_SERVER_URL"]
    run_id = os.environ["EVIDENCE_RUN_ID"]
    source_commit = git_output(source_dir, "rev-parse", "HEAD")
    source_tag = git_output(source_dir, "describe", "--tags", "--exact-match", "HEAD")

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "repository": repository,
        "tag": tag,
        "source_tag": source_tag,
        "tag_commit": source_commit,
        "head_commit": source_commit,
        "actor": os.environ["EVIDENCE_ACTOR"],
        "workflow": os.environ["EVIDENCE_WORKFLOW"],
        "run_id": int(run_id),
        "run_attempt": int(os.environ["EVIDENCE_RUN_ATTEMPT"]),
        "run_url": f"{server_url}/{repository}/actions/runs/{run_id}",
        "release": release,
        "assets": asset_records,
        "checksum_errors": checksum_errors,
        "has_sha256sums": checksums_path.exists(),
        "has_sbom": any(path.name.endswith(".sbom.spdx.json") for path in assets),
        "has_wheel": any(path.suffix == ".whl" for path in assets),
        "has_sdist": any(path.name.endswith(".tar.gz") for path in assets),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-metadata", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    evidence = build(
        release_metadata=args.release_metadata,
        assets_dir=args.assets,
        source_dir=args.source,
    )
    args.output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
