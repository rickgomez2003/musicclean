# ADR-0049: Archive Restore Verifies Before Recovery Actions

- **Status:** Accepted
- **Date:** 2026-08-05

MusicClean disaster recovery begins by restoring and verifying archived release
evidence. It does not automatically recreate or republish a GitHub Release.

The restore path retrieves the durable archive manifest/checksum and archive ZIP
from S3, verifies remote SHA-256 metadata, verifies the downloaded archive
digest, safely extracts the archive, and validates the restored release audit
evidence.

Only after a restore is proven internally consistent may a separate,
operator-approved recovery process use that evidence for reconstruction.

This separation prevents disaster-recovery verification from becoming an
implicit release mutation mechanism.
