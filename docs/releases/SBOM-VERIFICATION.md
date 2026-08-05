# SBOM Generation & Verification

MusicClean controlled releases include an SPDX JSON Software Bill of Materials.

The release asset is named:

`musicclean-<version>.sbom.spdx.json`

## Release process

The production release workflow:

1. builds the wheel and source distribution;
2. generates the SPDX JSON SBOM from the wheel;
3. validates the SBOM structure;
4. includes the SBOM in `SHA256SUMS`;
5. creates ordinary build provenance for the SBOM file;
6. creates an SBOM attestation binding the wheel to the SBOM;
7. publishes the SBOM with the release.

## Local SBOM validation

`python tools/release/verify_sbom.py --sbom PATH_TO_SBOM`

The validator requires an SPDX version, document namespace, and at least one
package.

## Attestation verification

Verify the wheel's GitHub attestations with:

`gh attestation verify PATH_TO_WHEEL --repo rickgomez2003/musicclean`

The wheel may carry both build-provenance and SBOM attestation predicates.

Checksum validation remains an independent required integrity check.
