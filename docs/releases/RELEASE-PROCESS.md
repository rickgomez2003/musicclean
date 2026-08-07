# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow.

## Controlled release

Controlled releases require an annotated tag matching the authoritative
MusicClean version. Published tags are immutable.

## Recovery operations

0.6.52 adds bounded, deduplicated, read-only history and trend analysis for
recovery alert delivery SLO evidence.

## Post-release verification

Post-release verification validates actual published artifacts.\n\n## Recovery alert delivery SLO alerting\n\n0.6.53 emits a provider-neutral alert decision without new write privileges.\n\n\n## Recovery alert delivery SLO routing\n\n0.6.54 emits route decision evidence without adding external delivery or repository mutation privileges.\n

## Recovery alert routed delivery

0.6.55 performs signed route-specific webhook delivery and retains a secret-safe delivery receipt with recovery drill evidence.

## Routed recovery alert delivery resilience

0.6.56 verifies bounded retry policy, route preservation, stable delivery identity, and secret-safe attempt history.
