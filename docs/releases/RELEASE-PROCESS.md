# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Dependency maintenance and security

Dependabot updates remain subject to Dependency Review, runtime `pip-audit`,
normal CI, branch protections, and the automated dependency merge policy.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow.

## Controlled release

Controlled releases require an annotated tag matching the authoritative
MusicClean version.

The production release workflow builds and validates artifacts, generates
checksums and the SPDX SBOM, smoke-tests the wheel, creates provenance/SBOM
attestations, and publishes the GitHub Release.

Published tags are immutable.

## Recovery drill automation

Recovery drills exercise the durable archive restore path without mutating
release state. They record PASS/FAIL results and elapsed recovery duration.

## Recovery objectives and SLOs

Passing recovery drill evidence is evaluated against explicit objectives for
recovery duration, successful-drill freshness, and successful-drill ratio.

Evaluation produces PASS, WARN, or FAIL status in
`recovery-slo-report.json`. Warning thresholds provide early operational signal
before a hard objective breach.

SLO evaluation is read-only and cannot publish releases, create/push tags,
change promotion state, or mutate archive objects.

## Post-release verification

Post-release verification validates actual published artifacts rather than only
source-tree state.
