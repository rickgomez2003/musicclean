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

## Promotion, rollback, evidence, and archival

Promotion and rollback modify channel metadata only. Audit evidence is
read-only. Verified evidence can be packaged into deterministic release archive
bundles.

## Durable archive export

Verified release archives may be exported through `Orion Durable Archive
Export`.

The first provider is AWS S3. GitHub OIDC supplies short-lived AWS credentials.
The workflow verifies the local archive, uploads the provider-neutral archive
bundle, writes the archive SHA-256 into remote object metadata, reads that
metadata back, and produces a durable export receipt.

Long-lived AWS access keys are prohibited by policy.

Durable export never modifies the published GitHub Release or release tag.

## Post-release verification

Post-release verification validates actual published artifacts rather than only
source-tree state.
