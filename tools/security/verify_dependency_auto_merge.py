"""Verify MusicClean automated dependency merge policy."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

PATCH = "version-update:semver-patch"
MINOR = "version-update:semver-minor"
MAJOR = "version-update:semver-major"


def _load_policy(root: Path) -> dict[str, Any]:
    path = root / "security" / "dependency-auto-merge-policy.toml"
    with path.open("rb") as stream:
        return tomllib.load(stream)


def verify(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []

    try:
        document = _load_policy(root)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return (f"unable to load dependency auto-merge policy: {exc}",)

    policy = document.get("policy")
    allowed = document.get("allowed_updates")
    manual = document.get("manual_updates")

    if not isinstance(policy, dict):
        return ("dependency auto-merge policy table is missing",)
    if not isinstance(allowed, dict):
        errors.append("allowed_updates table is missing")
        allowed = {}
    if not isinstance(manual, dict):
        errors.append("manual_updates table is missing")
        manual = {}

    if policy.get("actor") != "dependabot[bot]":
        errors.append("auto-merge actor must be dependabot[bot]")
    if policy.get("base_branch") != "develop":
        errors.append("auto-merge base branch must be develop")
    if policy.get("merge_method") != "squash":
        errors.append("auto-merge method must be squash")
    if policy.get("require_github_auto_merge") is not True:
        errors.append("GitHub auto-merge must be required")
    if policy.get("require_branch_protection") is not True:
        errors.append("branch protection must be required")
    if policy.get("allow_admin_bypass") is not False:
        errors.append("admin bypass must remain disabled")

    allowed_types = allowed.get("types")
    if allowed_types != [PATCH, MINOR]:
        errors.append("only patch and minor updates may be auto-merge eligible")

    manual_types = manual.get("types")
    if manual_types != [MAJOR]:
        errors.append("major dependency updates must remain manual")

    workflow = (root / ".github" / "workflows" / "orion-dependabot-auto-merge.yml").read_text(
        encoding="utf-8"
    )

    required = (
        "github.event.pull_request.user.login == 'dependabot[bot]'",
        "github.event.pull_request.base.ref == 'develop'",
        "dependabot/fetch-metadata@d7267f607e9d3fb96fc2fbe83e0af444713e90b7",
        PATCH,
        MINOR,
        MAJOR,
        'gh pr merge --auto --squash "$PR_URL"',
        "contents: write",
        "pull-requests: write",
    )
    for fragment in required:
        if fragment not in workflow:
            errors.append(f"auto-merge workflow missing {fragment}")

    forbidden = (
        "--admin",
        "pull_request_target",
        "version-update:semver-major' ||",
        "gh pr merge --merge ",
        "gh pr merge --rebase ",
    )
    for fragment in forbidden:
        if fragment in workflow:
            errors.append(f"auto-merge workflow contains forbidden pattern {fragment}")

    return tuple(errors)


def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("automated dependency merge policy verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
