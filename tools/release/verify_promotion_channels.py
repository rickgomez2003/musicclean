"""Verify MusicClean release promotion and channel policy."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CHANNELS = {"preview", "stable"}


def _load_policy(root: Path) -> dict[str, Any]:
    path = root / "release" / "channels.toml"
    with path.open("rb") as stream:
        return tomllib.load(stream)


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    try:
        document = _load_policy(root)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return (f"unable to load release channel policy: {exc}",)

    channels = document.get("channels")
    if not isinstance(channels, dict):
        return ("release channel table is missing",)

    preview = channels.get("preview")
    stable = channels.get("stable")

    if not isinstance(preview, dict):
        errors.append("preview channel is missing")
        preview = {}
    if not isinstance(stable, dict):
        errors.append("stable channel is missing")
        stable = {}

    expected_preview = {
        "environment": "release-preview",
        "prerelease": True,
        "latest": False,
    }
    expected_stable = {
        "environment": "release-stable",
        "prerelease": False,
        "latest": True,
    }
    if preview != expected_preview:
        errors.append("preview channel policy does not match expected values")
    if stable != expected_stable:
        errors.append("stable channel policy does not match expected values")

    workflow = (root / ".github" / "workflows" / "orion-release-promotion.yml").read_text(
        encoding="utf-8"
    )

    required = (
        "workflow_dispatch:",
        "release-${{ inputs.channel }}",
        "inputs.channel == 'preview'",
        "inputs.channel == 'stable'",
        "--prerelease \\",
        "--latest=false",
        "--prerelease=false",
        "--latest",
        "contents: write",
        "verify_promotion_channels.py",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"release promotion workflow missing {fragment}")

    forbidden = (
        "python -m build",
        "actions/attest",
        "anchore/sbom-action",
        "gh release create",
        "--admin",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"release promotion workflow contains forbidden pattern {fragment}")

    return tuple(errors)


def _release(repository: str, tag: str) -> dict[str, Any]:
    command = [
        "gh",
        "api",
        f"repos/{repository}/releases/tags/{tag}",
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ValueError(f"unable to resolve published release {tag}: {detail}")

    data = json.loads(completed.stdout)
    if not isinstance(data, dict):
        raise ValueError("GitHub release response must be an object")
    return data


def verify_promotion(repository: str, tag: str, channel: str) -> tuple[str, ...]:
    errors: list[str] = []

    if channel not in CHANNELS:
        return (f"unsupported release channel: {channel}",)

    if not tag.startswith("v"):
        errors.append("release tag must begin with v")

    try:
        release = _release(repository, tag)
    except (ValueError, json.JSONDecodeError) as exc:
        return (*errors, str(exc))

    if release.get("draft") is True:
        errors.append("draft releases cannot be promoted")

    if release.get("tag_name") != tag:
        errors.append("published release tag does not match requested tag")

    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag")
    parser.add_argument("--channel", choices=sorted(CHANNELS))
    parser.add_argument("--repository")
    args = parser.parse_args()

    errors = list(verify_configuration())

    supplied = (args.tag, args.channel, args.repository)
    if any(value is not None for value in supplied):
        if not all(value is not None for value in supplied):
            errors.append("--tag, --channel and --repository must be supplied together")
        else:
            errors.extend(
                verify_promotion(
                    repository=args.repository,
                    tag=args.tag,
                    channel=args.channel,
                )
            )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.tag is None:
        print("release promotion and channel policy verified")
    else:
        print(f"release {args.tag} may be promoted to {args.channel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
