# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow. Candidate workflows do not publish
production attestations.

## Publish a controlled release

An annotated tag is created only from the exact merged commit that passed
release-candidate validation.

The production release workflow:

1. builds and validates the wheel and source distribution;
2. generates and validates an SPDX JSON SBOM for the wheel;
3. generates SHA256SUMS including the SBOM;
4. smoke-tests the built wheel;
5. creates build-provenance attestations for release assets;
6. creates an SBOM attestation binding the wheel to its SBOM;
7. publishes all assets to the GitHub Release.

Published tags are immutable.

## Verify provenance and SBOM

For a downloaded wheel:

`gh attestation verify PATH_TO_WHEEL --repo rickgomez2003/musicclean`

Validate a downloaded SBOM with:

`python tools/release/verify_sbom.py --sbom PATH_TO_SBOM`

Artifact attestation and SBOM verification complement rather than replace
SHA-256 checksum verification.

## Post-release verification

Post-release verification downloads actual published release assets, verifies
checksums, installs the published wheel into a clean environment, starts Orion,
and verifies `/v1/health`.

## Stable release operations

Patch and hotfix releases follow the same candidate, provenance, SBOM, and
post-release verification path.
