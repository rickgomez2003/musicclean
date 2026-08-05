"""Verify MusicClean stable-channel rollback and recovery policy."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _load_policy(root: Path) -> dict[str, Any]:
    path = root / "release" / "recovery.toml"
    with path.open("rb") as stream:
        return tomllib.load(stream)


def verify_configuration(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []
    try:
        document = _load_policy(root)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return (f"unable to load rollback policy: {exc}",)

    rollback = document.get("rollback")
    if not isinstance(rollback, dict):
        return ("rollback policy table is missing",)

    expected = {
        "environment": "release-stable",
        "require_current_latest": True,
        "demote_current_to_prerelease": True,
        "restore_target_as_latest": True,
        "restore_target_as_prerelease": False,
        "preserve_artifacts": True,
        "preserve_tags": True,
    }
    if rollback != expected:
        errors.append("rollback policy does not match expected safe values")

    workflow = (root / ".github" / "workflows" / "orion-release-rollback.yml").read_text(
        encoding="utf-8"
    )

    required = (
        "workflow_dispatch:",
        "name: release-stable",
        "verify_rollback_recovery.py",
        "Demote previous stable release",
        "Restore recovery release as stable",
        "--latest=false",
        "--prerelease=false",
        "--verify-result",
        "contents: write",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"rollback workflow missing {fragment}")

    forbidden = (
        "python -m build",
        "gh release create",
        "gh release delete",
        "gh release upload",
        "git tag -d",
        "git push --delete",
        "actions/attest",
        "anchore/sbom-action",
        "--admin",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"rollback workflow contains forbidden pattern {fragment}")
    return tuple(errors)


def _api(repository: str, endpoint: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["gh", "api", f"repos/{repository}/{endpoint}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ValueError(detail)
    data = json.loads(completed.stdout)
    if not isinstance(data, dict):
        raise ValueError("GitHub API response must be an object")
    return data


def verify_request(repository: str, current_tag: str, recovery_tag: str) -> tuple[str, ...]:
    errors: list[str] = []
    if current_tag == recovery_tag:
        return ("current and recovery tags must be different",)
    if not current_tag.startswith("v"):
        errors.append("current release tag must begin with v")
    if not recovery_tag.startswith("v"):
        errors.append("recovery release tag must begin with v")

    try:
        current = _api(repository, f"releases/tags/{current_tag}")
        recovery = _api(repository, f"releases/tags/{recovery_tag}")
        latest = _api(repository, "releases/latest")
    except (ValueError, json.JSONDecodeError) as exc:
        return (*errors, f"unable to resolve release state: {exc}")

    if current.get("draft") is True:
        errors.append("current release cannot be a draft")
    if recovery.get("draft") is True:
        errors.append("recovery release cannot be a draft")
    if current.get("tag_name") != current_tag:
        errors.append("current release tag does not match request")
    if recovery.get("tag_name") != recovery_tag:
        errors.append("recovery release tag does not match request")
    if latest.get("tag_name") != current_tag:
        errors.append("current release is not GitHub's latest release")
    return tuple(errors)


def verify_result(repository: str, current_tag: str, recovery_tag: str) -> tuple[str, ...]:
    errors: list[str] = []
    try:
        current = _api(repository, f"releases/tags/{current_tag}")
        recovery = _api(repository, f"releases/tags/{recovery_tag}")
        latest = _api(repository, "releases/latest")
    except (ValueError, json.JSONDecodeError) as exc:
        return (f"unable to resolve release state: {exc}",)

    if current.get("prerelease") is not True:
        errors.append("demoted release is not marked prerelease")
    if recovery.get("prerelease") is not False:
        errors.append("recovery release is still marked prerelease")
    if latest.get("tag_name") != recovery_tag:
        errors.append("recovery release is not GitHub's latest release")
    return tuple(errors)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-tag")
    parser.add_argument("--recovery-tag")
    parser.add_argument("--repository")
    parser.add_argument("--verify-result", action="store_true")
    args = parser.parse_args()

    errors = list(verify_configuration())
    supplied = (args.current_tag, args.recovery_tag, args.repository)

    if any(value is not None for value in supplied):
        if not all(value is not None for value in supplied):
            errors.append(
                "--current-tag, --recovery-tag and --repository must be supplied together"
            )
        elif args.verify_result:
            errors.extend(verify_result(args.repository, args.current_tag, args.recovery_tag))
        else:
            errors.extend(verify_request(args.repository, args.current_tag, args.recovery_tag))
    elif args.verify_result:
        errors.append("--verify-result requires release arguments")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.current_tag is None:
        print("release rollback and recovery policy verified")
    elif args.verify_result:
        print(f"release rollback to {args.recovery_tag} verified")
    else:
        print(f"rollback request from {args.current_tag} to {args.recovery_tag} verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
