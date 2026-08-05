# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Dependency maintenance and merge policy

Dependabot proposes scheduled dependency updates. Eligible PATCH and MINOR
Dependabot version updates targeting `develop` may have GitHub auto-merge
enabled, while MAJOR updates remain manual.

## Dependency security gate

Dependency changes remain subject to Dependency Review, runtime `pip-audit`,
normal CI, and repository branch protections.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow.

## Controlled release

Controlled releases require an annotated tag matching the authoritative
MusicClean version.

The production release workflow builds and validates distribution artifacts,
generates checksums and the SPDX SBOM, smoke-tests the wheel, creates
provenance/SBOM attestations, and publishes the GitHub Release.

Published tags are immutable.

## Promotion

Release creation and release promotion are separate operations.

An existing published release may be promoted through the `preview` or `stable`
channel using the `Orion Release Promotion` workflow.

Promotion changes GitHub Release metadata only. It never rebuilds, replaces, or
re-attests release artifacts.

GitHub Environments named `release-preview` and `release-stable` form the
repository-side protection boundary for channel promotion.

## Post-release verification

Post-release verification validates actual published artifacts rather than
only source-tree state.
