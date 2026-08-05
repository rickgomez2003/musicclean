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

## Promotion, rollback, evidence, archival, and durable export

Promotion and rollback modify channel metadata only. Audit evidence is
read-only. Verified evidence can be packaged into deterministic release
archives and exported to durable S3 storage using GitHub OIDC.

## Archive restore and disaster recovery

`Orion Archive Restore` performs the reverse integrity path from durable S3
storage.

The workflow retrieves the archive metadata and ZIP, verifies remote and local
SHA-256 identity, verifies the archive bundle, safely extracts the evidence,
validates the restored audit evidence, and generates a restore receipt.

Restore never automatically publishes a GitHub Release, creates/pushes tags, or
modifies release-channel metadata.

Any future release reconstruction must be a separate operator-approved action
after restore verification succeeds.

## Post-release verification

Post-release verification validates actual published artifacts rather than only
source-tree state.
