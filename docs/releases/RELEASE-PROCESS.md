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

## Promotion, rollback, and evidence

Promotion and rollback change release-channel metadata only. Audit evidence is
collected separately and read-only from an existing published release.

## Retention and archival

Verified release audit evidence may be packaged by `Orion Release Archive` into
a deterministic provider-neutral archive bundle.

The archive contains the original evidence bundle, an archive manifest, and
SHA-256 integrity metadata.

Operational retention is 90 days. Long-term retention is at least 2555 days
and requires external durable export before the GitHub Actions artifact expires.

Archival never modifies the published GitHub Release or tag.

## Post-release verification

Post-release verification validates actual published artifacts rather than only
source-tree state.
