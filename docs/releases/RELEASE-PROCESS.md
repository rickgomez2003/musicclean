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

Recovery drills restore durable evidence and evaluate recovery objectives.
Alert generation remains part of recovery analysis.

Beginning with 0.6.49, external alert delivery is privilege-separated into a
dedicated downstream job and environment. Delivery retries only transient
failures and records a deterministic delivery identifier plus attempt history.

## Post-release verification

Post-release verification validates actual published artifacts rather than only
source-tree state.
