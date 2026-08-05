# Book 14 — Operations

0.6.36 adds dependency update automation.

Dependabot now proposes routine updates for Python packages, GitHub Actions,
and the root runtime Dockerfile. Version-update pull requests target `develop`
on staggered weekly schedules with bounded open-PR counts.

Automation is intentionally proposal-only. Every dependency update continues
through the same security and quality gates established by prior Orion
milestones:

- normal CI and typing/tests;
- GitHub Dependency Review;
- isolated runtime `pip-audit`;
- Release Candidate validation;
- provenance and SBOM release controls.

Python minor and patch updates are grouped to reduce maintenance noise while
major updates remain separately reviewable.
