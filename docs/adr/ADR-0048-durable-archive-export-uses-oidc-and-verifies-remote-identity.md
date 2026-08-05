# ADR-0048: Durable Archive Export Uses OIDC and Verifies Remote Identity

- **Status:** Accepted
- **Date:** 2026-08-05

MusicClean exports verified release archives to AWS S3 using GitHub OIDC and a
repository-scoped IAM role.

Long-lived AWS access keys are not part of the release process.

The export workflow verifies the local archive before transfer, writes the
archive SHA-256 into S3 object metadata, reads the metadata back after upload,
and requires the remote value to match the verified local archive digest.

A machine-readable export receipt records the destination bucket/key identity,
source archive run, export run, retention class, and verified digest.

The export operation does not mutate GitHub Releases or release tags.
