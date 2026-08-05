# ADR-0040: Release SBOM Is Generated and Attested With Release Artifacts

- **Status:** Accepted
- **Date:** 2026-08-04

Every controlled MusicClean release includes a machine-readable SPDX JSON
Software Bill of Materials.

The SBOM is generated from the built wheel using Syft through
`anchore/sbom-action`.

The SBOM is a release asset, is included in `SHA256SUMS`, and is itself covered
by the ordinary release build-provenance attestation.

A separate GitHub SBOM attestation binds the built wheel to the SPDX document.

The responsibilities remain distinct:

- checksums establish byte integrity;
- build provenance establishes where and how artifacts were produced;
- the SBOM describes the software components represented by the artifact.

Release Candidate workflows validate policy but do not publish production SBOM
attestations.
