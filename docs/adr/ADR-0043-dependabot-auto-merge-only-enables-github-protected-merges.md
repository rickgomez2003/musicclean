# ADR-0043: Dependabot Auto-Merge Only Enables GitHub-Protected Merges

- **Status:** Accepted
- **Date:** 2026-08-05

MusicClean permits automated merge only for low-risk Dependabot version updates.

Eligible updates are semantic-version PATCH and MINOR updates authored by
`dependabot[bot]` and targeting `develop`.

The automation does not directly bypass repository protections. It enables
GitHub auto-merge with squash merging. GitHub performs the merge only when the
target branch's configured merge requirements are satisfied.

MAJOR dependency updates remain manual.

The workflow never uses an administrative bypass and does not use
`pull_request_target`.

Repository configuration is therefore part of the control boundary:

- GitHub auto-merge must be enabled;
- `develop` must require the intended CI/security checks;
- maintainers retain control of branch protection/rulesets.
