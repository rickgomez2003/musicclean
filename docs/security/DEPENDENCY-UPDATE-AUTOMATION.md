# Dependency Update Automation

MusicClean uses Dependabot version updates to keep supported dependencies
current without bypassing release or security controls.

## Ecosystems

Dependabot monitors:

- Python dependencies declared from the repository root;
- GitHub Actions used by repository workflows;
- the root Dockerfile.

## Target branch

Routine version-update pull requests target `develop`.

This keeps dependency maintenance inside the same integration branch used for
Orion feature development.

## Schedule

Update checks are staggered:

- Python: Monday at 06:00 UTC;
- GitHub Actions: Tuesday at 06:00 UTC;
- Docker: Wednesday at 06:00 UTC.

Staggering reduces simultaneous update noise and makes failed dependency gates
easier to attribute.

## Pull-request limits

- Python: maximum 5 open version-update PRs;
- GitHub Actions: maximum 5;
- Docker: maximum 3.

## Grouping

Python minor and patch updates are grouped. Major Python version changes remain
separate so they receive explicit compatibility review.

GitHub Actions updates are grouped to reduce workflow-maintenance noise.

## Security relationship

Dependabot proposes updates only. It does not override branch protections or
merge decisions.

Each update PR must still pass:

- normal CI and type/test quality gates;
- GitHub Dependency Review;
- the isolated Python runtime `pip-audit` gate where applicable;
- Orion Release Candidate validation;
- other configured repository protections.

Dependabot security updates remain distinct from scheduled version updates and
continue to use GitHub's security-update mechanisms.
