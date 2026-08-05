# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Dependency maintenance and security

Dependency changes remain subject to security review, runtime auditing, normal
CI, branch protections, and dependency merge policy.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow.

## Controlled release

Controlled releases require an annotated tag matching the authoritative
MusicClean version. Published tags are immutable.

## Recovery operations

Recovery drills exercise durable archive restoration without mutating release
state. Historical evidence supports recovery SLO and trend evaluation.

0.6.47 maps SLO/trend evidence into provider-neutral alerts and GitHub Actions
summaries. External alert delivery remains disabled. No release, tag,
promotion, archive, issue, or pull-request mutation permission is introduced.

## Post-release verification

Post-release verification validates actual published artifacts rather than only
source-tree state.
