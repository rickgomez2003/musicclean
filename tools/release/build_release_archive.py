"""Build a deterministic release archive from verified release evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _zip_directory(source: Path, destination: Path) -> None:
    files = sorted(path for path in source.rglob("*") if path.is_file())
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(relative, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def build(evidence_dir: Path, output_dir: Path) -> dict[str, Any]:
    evidence_path = evidence_dir / "release-audit-evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        raise ValueError("release audit evidence must be a JSON object")

    tag = os.environ["ARCHIVE_TAG"]
    if evidence.get("tag") != tag:
        raise ValueError("archive tag does not match release audit evidence")

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_tag = tag.replace("/", "_")
    archive_path = output_dir / f"musicclean-{safe_tag}-release-evidence.zip"
    _zip_directory(evidence_dir, archive_path)

    archive_digest = sha256(archive_path)
    checksum_path = output_dir / "release-archive.SHA256SUMS"
    checksum_path.write_text(
        f"{archive_digest}  {archive_path.name}\n",
        encoding="utf-8",
    )

    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "repository": os.environ["ARCHIVE_REPOSITORY"],
        "tag": tag,
        "retention_class": os.environ["ARCHIVE_RETENTION_CLASS"],
        "source_evidence_run_id": int(os.environ["ARCHIVE_SOURCE_RUN_ID"]),
        "archive_run_id": int(os.environ["ARCHIVE_RUN_ID"]),
        "archive_name": archive_path.name,
        "archive_sha256": archive_digest,
        "source_evidence_sha256": sha256(evidence_path),
    }
    manifest_path = output_dir / "release-archive-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = build(args.evidence_dir, args.output_dir)
    print(manifest["archive_name"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
