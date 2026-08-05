# ADR-0039: Release Artifacts Carry GitHub Build Provenance

- **Status:** Accepted
- **Date:** 2026-08-04

Controlled MusicClean release artifacts carry GitHub artifact attestations.

Checksums and provenance have different responsibilities:

- SHA-256 checksums detect changes to artifact bytes.
- Build provenance establishes which repository, commit, workflow and GitHub
  identity produced the attested artifact.

The release workflow uses GitHub OIDC-backed artifact attestations for the
wheel, source distribution, and SHA256SUMS.

Only the production release workflow receives attestation-writing permissions.
Pull-request Release Candidate workflows remain read-only with respect to
attestation publication.

Published tags remain immutable.
