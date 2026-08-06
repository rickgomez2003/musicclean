# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Dependency maintenance and security

Dependency changes remain subject to security review, runtime auditing, normal CI, branch protections, and dependency merge policy.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the `Orion Release Candidate` workflow.

## Controlled release

Controlled releases require an annotated tag matching the authoritative MusicClean version. Published tags are immutable.

## Recovery operations

Recovery drills restore durable evidence and evaluate recovery objectives. External alert delivery is privilege separated and artifact observed.

0.6.51 evaluates recovery alert delivery SLOs from observability evidence using policy-driven thresholds and minimum-sample gating.

## Post-release verification

Post-release verification validates actual published artifacts rather than only source-tree state.
