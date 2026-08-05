# Automated Dependency Merge Policy

## Purpose

Routine dependency maintenance should not require a maintainer to click Merge
for every low-risk update, but automation must not bypass security or quality
controls.

## Eligibility

Automatic merge may be enabled only when all of the following are true:

- pull request author is `dependabot[bot]`;
- base branch is `develop`;
- Dependabot classifies the update as semantic-version PATCH or MINOR.

Semantic-version MAJOR updates remain manual.

## Merge behavior

The workflow runs:

`gh pr merge --auto --squash`

This enables GitHub auto-merge. It is not an administrative merge and does not
override branch protections.

The actual merge occurs only when GitHub considers the pull request mergeable
under the repository's configured rules.

## Required repository configuration

Maintainers must enable **Allow auto-merge** in repository settings.

The `develop` branch protection/ruleset must require the security and quality
checks that should gate automated dependency changes. At minimum, include:

- CI;
- Orion Quality;
- Orion Dependency Security / Dependency Review;
- Orion Dependency Security / Python Runtime Audit.

Release Candidate and other required checks may also be included according to
repository policy.

## Explicitly forbidden

- administrative bypass (`--admin`);
- automatic merge of semantic-version MAJOR updates;
- `pull_request_target` for this workflow;
- weakening required checks solely to make auto-merge succeed.

## Failure behavior

If a required check fails, GitHub auto-merge remains pending and the pull
request does not merge.

If Dependabot updates the branch, GitHub reruns the normal PR checks before the
merge requirements can be satisfied.
