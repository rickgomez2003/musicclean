# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow. The candidate workflow derives its version
from the authoritative package version and does not publish production
attestations.

## Publish a controlled release

An annotated tag is created only from the exact merged commit that passed
release-candidate validation.

The production release workflow builds and validates the wheel and source
distribution, generates SHA256SUMS, creates GitHub build-provenance
attestations, and then publishes the GitHub Release.

Published tags are immutable.

## Verify provenance

For a downloaded release artifact:

`gh attestation verify PATH_TO_ARTIFACT --repo rickgomez2003/musicclean`

Artifact attestation verification complements rather than replaces SHA-256
checksum verification.

## Post-release verification

Post-release verification downloads the actual published release assets,
verifies checksums, installs the published wheel into a clean environment,
starts Orion, and verifies `/v1/health`.

## Stable release operations

Patch and hotfix releases follow the same candidate, controlled-release,
provenance, and post-release verification path.
