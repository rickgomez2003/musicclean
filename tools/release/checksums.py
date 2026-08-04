"""Generate SHA-256 checksums for built release artifacts."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: checksums.py DIST_DIR", file=sys.stderr)
        return 2

    dist = Path(sys.argv[1])
    artifacts = sorted(
        path for path in dist.iterdir() if path.is_file() and path.name != "SHA256SUMS"
    )
    if not artifacts:
        print("no release artifacts found", file=sys.stderr)
        return 1

    lines = [f"{sha256(path)}  {path.name}" for path in artifacts]
    (dist / "SHA256SUMS").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
