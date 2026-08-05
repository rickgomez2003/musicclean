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

The production release workflow builds and validates distribution artifacts,
generates checksums and the SPDX SBOM, smoke-tests the wheel, creates
provenance/SBOM attestations, and publishes the GitHub Release.

Published tags are immutable.

## Promotion and rollback

Promotion and rollback change release-channel metadata only and never rebuild
or replace immutable release artifacts.

## Audit evidence

Release audit evidence is collected separately using the read-only
`Orion Release Audit Evidence` workflow.

Evidence collection checks out the exact published tag, downloads release
assets, validates SHA256SUMS, records release/workflow identity, verifies the
expected release components, and uploads a machine-readable evidence bundle.

Evidence collection never edits the audited GitHub Release.

## Post-release verification

Post-release verification validates actual published artifacts rather than only
source-tree state.
