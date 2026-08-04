"""Validate release-candidate artifacts before publication."""

from __future__ import annotations

import argparse
import re
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

_WHEEL_RE = re.compile(r"^musicclean-(\d+\.\d+\.\d+)-py3-none-any\.whl$")
_SDIST_RE = re.compile(r"^musicclean-(\d+\.\d+\.\d+)\.tar\.gz$")


@dataclass(frozen=True, slots=True)
class CandidateArtifacts:
    wheel: Path
    sdist: Path
    checksums: Path


def discover_artifacts(dist: Path, expected: str) -> CandidateArtifacts:
    wheels = sorted(dist.glob("musicclean-*.whl"))
    sdists = sorted(dist.glob("musicclean-*.tar.gz"))
    checksums = dist / "SHA256SUMS"

    if len(wheels) != 1:
        raise ValueError("release candidate must contain exactly one wheel")
    if len(sdists) != 1:
        raise ValueError("release candidate must contain exactly one source distribution")
    if not checksums.is_file():
        raise ValueError("SHA256SUMS is required")

    wheel_match = _WHEEL_RE.fullmatch(wheels[0].name)
    sdist_match = _SDIST_RE.fullmatch(sdists[0].name)
    if wheel_match is None or wheel_match.group(1) != expected:
        raise ValueError("wheel version does not match expected release candidate")
    if sdist_match is None or sdist_match.group(1) != expected:
        raise ValueError("sdist version does not match expected release candidate")

    return CandidateArtifacts(wheels[0], sdists[0], checksums)


def wheel_metadata_version(wheel: Path) -> str:
    with zipfile.ZipFile(wheel) as archive:
        names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(names) != 1:
            raise ValueError("wheel must contain exactly one METADATA file")
        text = archive.read(names[0]).decode("utf-8")

    for line in text.splitlines():
        if line.startswith("Version: "):
            return line.removeprefix("Version: ").strip()
    raise ValueError("wheel metadata does not contain a Version field")


def sdist_contains_version_source(sdist: Path) -> bool:
    with tarfile.open(sdist, "r:gz") as archive:
        return any(
            member.name.endswith("/src/musicclean/version.py") for member in archive.getmembers()
        )


def checksums_cover_artifacts(artifacts: CandidateArtifacts) -> bool:
    text = artifacts.checksums.read_text(encoding="utf-8")
    return artifacts.wheel.name in text and artifacts.sdist.name in text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--expected", required=True)
    args = parser.parse_args()

    try:
        artifacts = discover_artifacts(args.dist, args.expected)
        if wheel_metadata_version(artifacts.wheel) != args.expected:
            raise ValueError("wheel metadata version does not match expected")
        if not sdist_contains_version_source(artifacts.sdist):
            raise ValueError("sdist does not contain authoritative version source")
        if not checksums_cover_artifacts(artifacts):
            raise ValueError("SHA256SUMS does not cover wheel and sdist")
    except (OSError, ValueError, zipfile.BadZipFile, tarfile.TarError) as exc:
        print(f"release candidate validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"release candidate {args.expected} validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
