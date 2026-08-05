"""Verify MusicClean dependency update automation policy."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ECOSYSTEMS = {"pip", "github-actions", "docker"}


def _load(root: Path) -> dict[str, Any]:
    path = root / ".github" / "dependabot.yml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("dependabot configuration root must be a mapping")
    return document


def verify(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    try:
        document = _load(root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return (f"unable to load dependabot configuration: {exc}",)

    if document.get("version") != 2:
        errors.append("dependabot configuration must use version 2")

    updates = document.get("updates")
    if not isinstance(updates, list):
        return (*errors, "dependabot updates must be a list")

    seen: set[str] = set()

    for item in updates:
        if not isinstance(item, dict):
            errors.append("dependabot update entry must be a mapping")
            continue

        ecosystem = item.get("package-ecosystem")
        if not isinstance(ecosystem, str):
            errors.append("dependabot update entry is missing package-ecosystem")
            continue

        seen.add(ecosystem)

        if item.get("directory") != "/":
            errors.append(f"{ecosystem} must monitor the repository root")

        if item.get("target-branch") != "develop":
            errors.append(f"{ecosystem} updates must target develop")

        schedule = item.get("schedule")
        if not isinstance(schedule, dict) or schedule.get("interval") != "weekly":
            errors.append(f"{ecosystem} must use a weekly schedule")

        limit = item.get("open-pull-requests-limit")
        if not isinstance(limit, int) or limit < 1 or limit > 5:
            errors.append(f"{ecosystem} open pull request limit must be 1 through 5")

    missing = EXPECTED_ECOSYSTEMS - seen
    if missing:
        errors.append("dependabot ecosystems missing: " + ", ".join(sorted(missing)))

    pip_entry = next(
        (
            item
            for item in updates
            if isinstance(item, dict) and item.get("package-ecosystem") == "pip"
        ),
        None,
    )
    if not isinstance(pip_entry, dict):
        errors.append("pip update configuration is missing")
    else:
        if pip_entry.get("versioning-strategy") != "increase-if-necessary":
            errors.append("pip updates must use increase-if-necessary")

        groups = pip_entry.get("groups")
        if not isinstance(groups, dict) or "python-minor-patch" not in groups:
            errors.append("pip minor/patch update group is missing")

    actions_entry = next(
        (
            item
            for item in updates
            if isinstance(item, dict) and item.get("package-ecosystem") == "github-actions"
        ),
        None,
    )
    if not isinstance(actions_entry, dict):
        errors.append("GitHub Actions update configuration is missing")
    else:
        groups = actions_entry.get("groups")
        if not isinstance(groups, dict) or "github-actions" not in groups:
            errors.append("GitHub Actions update group is missing")

    return tuple(errors)


def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("dependency update automation verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
