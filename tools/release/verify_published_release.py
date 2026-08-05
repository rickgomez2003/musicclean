"""Verify downloaded assets from a published MusicClean release."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_HASH_RE = re.compile(r"^([0-9a-f]{64})\s+(.+)$")


@dataclass(frozen=True, slots=True)
class PublishedRelease:
    tag: str
    version: str
    wheel: Path
    sdist: Path
    checksums: Path


def expected_asset_names(version: str) -> tuple[str, str]:
    return (
        f"musicclean-{version}-py3-none-any.whl",
        f"musicclean-{version}.tar.gz",
    )


def discover_downloaded_release(directory: Path, *, tag: str) -> PublishedRelease:
    version = tag.removeprefix("v")
    wheel_name, sdist_name = expected_asset_names(version)
    wheel = directory / wheel_name
    sdist = directory / sdist_name
    checksums = directory / "SHA256SUMS"

    missing = [p.name for p in (wheel, sdist, checksums) if not p.is_file()]
    if missing:
        raise ValueError("missing published release assets: " + ", ".join(missing))

    return PublishedRelease(tag, version, wheel, sdist, checksums)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_checksums(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = _HASH_RE.fullmatch(line)
        if match is None:
            raise ValueError(f"invalid checksum line: {raw_line}")
        digest, filename = match.groups()
        parsed[filename] = digest
    return parsed


def verify_checksums(release: PublishedRelease) -> tuple[str, ...]:
    expected = parse_checksums(release.checksums)
    errors: list[str] = []
    for artifact in (release.wheel, release.sdist):
        recorded = expected.get(artifact.name)
        if recorded is None:
            errors.append(f"checksum missing for {artifact.name}")
        elif sha256(artifact) != recorded:
            errors.append(f"checksum mismatch for {artifact.name}")
    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    try:
        release = discover_downloaded_release(args.directory, tag=args.tag)
        errors = verify_checksums(release)
    except (OSError, ValueError) as exc:
        print(f"published release verification failed: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"published release {release.tag} verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
