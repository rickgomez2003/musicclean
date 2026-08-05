# Book 14 — Operations

0.6.43 adds archive restore and disaster recovery verification.

Durable S3 archives can now be restored through a protected GitHub workflow.
The restore path authenticates through GitHub OIDC, retrieves the manifest,
checksum, and archive bundle, verifies S3 SHA-256 metadata, verifies the
downloaded archive digest, safely extracts the deterministic archive, and
validates the recovered release audit evidence.

A restore receipt records the source destination, release identity, archive
digest, and verification results.

Restore is deliberately evidence-only. It does not republish releases, recreate
tags, or modify release channels automatically.
