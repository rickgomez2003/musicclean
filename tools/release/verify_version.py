"""Verify release/package/tag version consistency."""

from __future__ import annotations

import argparse
import re
import sys

from musicclean import __version__

_TAG_PATTERN = re.compile(r"^v?(\d+\.\d+\.\d+)$")


def normalize_tag(tag: str) -> str:
    match = _TAG_PATTERN.fullmatch(tag.strip())
    if match is None:
        raise ValueError("release tag must look like vMAJOR.MINOR.PATCH")
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected")
    parser.add_argument("--tag")
    args = parser.parse_args()

    expected = args.expected or __version__
    if expected != __version__:
        print(
            f"version mismatch: package={__version__} expected={expected}",
            file=sys.stderr,
        )
        return 1

    if args.tag is not None:
        try:
            tag_version = normalize_tag(args.tag)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if tag_version != __version__:
            print(
                f"version mismatch: package={__version__} tag={tag_version}",
                file=sys.stderr,
            )
            return 1

    print(__version__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
