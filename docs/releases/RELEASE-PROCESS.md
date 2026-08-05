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
state.

Recovery objectives evaluate drill evidence for duration, successful-drill
freshness, and success ratio.

0.6.46 collects prior drill artifacts using `actions: read`, builds bounded
cross-run history, and generates rolling recovery trend evidence. No release,
tag, promotion, or archive mutation permission is introduced.

## Post-release verification

Post-release verification validates actual published artifacts rather than only
source-tree state.
