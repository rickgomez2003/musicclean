# Book 14 — Operations

0.6.34 adds controlled-release SBOM generation and attestation.

The production release workflow generates an SPDX JSON SBOM from the built
wheel with Syft. The SBOM is validated before publication, included in
`SHA256SUMS`, covered by ordinary build provenance, and bound to the wheel by a
GitHub SBOM attestation.

The release trust model now has three distinct layers:

- SHA-256 checksums: artifact byte integrity;
- build provenance: repository, commit, and workflow identity;
- SPDX SBOM: software component inventory.

The SBOM ships as a normal release asset and can be validated with
`tools/release/verify_sbom.py`.
