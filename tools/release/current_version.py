"""Expose the authoritative MusicClean version to release automation."""

from __future__ import annotations

import argparse
from pathlib import Path

from musicclean import __version__


def write_github_output(path: Path, version: str) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(f"version={version}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    if args.github_output is not None:
        write_github_output(args.github_output, __version__)

    print(__version__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
