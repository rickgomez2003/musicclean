# ADR-0042: Dependency Updates Are Automated but Remain Gated

- **Status:** Accepted
- **Date:** 2026-08-05

MusicClean uses Dependabot to propose routine dependency updates, but automatic
proposal does not imply automatic acceptance.

Dependabot monitors:

- Python package dependencies;
- GitHub Actions;
- the root runtime Dockerfile.

Update pull requests target `develop` and use staggered weekly schedules.
Python minor and patch updates are grouped to reduce pull-request noise, while
major updates remain separately reviewable.

Every Dependabot pull request remains subject to the same controls as human
changes, including CI, Dependency Review, runtime `pip-audit`, release
candidate validation, and normal branch protections.

This separates responsibilities:

- Dependabot detects available updates and proposes changes;
- security and quality gates determine whether those changes are acceptable;
- maintainers retain merge authority.
