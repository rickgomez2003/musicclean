"""Resolve manual or scheduled recovery drill target inputs."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def _resolve(input_value: str | None, default_value: str | None, label: str) -> str:
    value = (input_value or "").strip() or (default_value or "").strip()
    if not value:
        raise ValueError(f"{label} is required for the recovery drill")
    return value


def resolve() -> tuple[str, str]:
    tag = _resolve(
        os.environ.get("INPUT_TAG"),
        os.environ.get("DEFAULT_TAG"),
        "recovery drill tag",
    )
    retention_class = _resolve(
        os.environ.get("INPUT_RETENTION_CLASS"),
        os.environ.get("DEFAULT_RETENTION_CLASS"),
        "recovery drill retention class",
    )
    if retention_class not in {"operational", "long-term"}:
        raise ValueError("recovery drill retention class is invalid")
    if not tag.startswith("v"):
        raise ValueError("recovery drill tag must start with v")
    return tag, retention_class


def write_github_output(path: Path, tag: str, retention_class: str) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(f"tag={tag}\n")
        stream.write(f"retention_class={retention_class}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--github-output", type=Path, required=True)
    args = parser.parse_args()

    tag, retention_class = resolve()
    write_github_output(args.github_output, tag, retention_class)
    print(f"Recovery drill target: {tag} ({retention_class})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
