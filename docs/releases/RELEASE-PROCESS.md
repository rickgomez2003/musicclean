# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Dependency maintenance and merge policy

Dependabot proposes scheduled dependency updates. Eligible PATCH and MINOR
updates targeting `develop` may have GitHub auto-merge enabled while MAJOR
updates remain manual.

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

Release promotion changes channel metadata on an existing published release.
Preview and stable promotion never rebuild or replace artifacts.

## Rollback and recovery

Rollback restores the stable channel to a previously published release. The
current stable/latest release is demoted to prerelease/non-latest and the
selected recovery release is promoted to non-prerelease/latest.

Rollback uses the protected `release-stable` GitHub Environment and never
rebuilds artifacts, replaces assets, deletes tags, or creates a replacement
release.

After rollback, fix-forward remediation uses the normal controlled-release path
with a new version and immutable tag.

## Post-release verification

Post-release verification validates actual published artifacts rather than only
source-tree state.
