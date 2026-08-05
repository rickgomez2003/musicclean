# Book 14 — Operations

0.6.42 adds durable archive export.

Verified 0.6.41 release archive bundles can be exported to AWS S3 through a
protected GitHub Environment. Authentication uses GitHub OIDC and a short-lived
AWS role session instead of static AWS access keys.

The archive is verified before export. Its SHA-256 is written to S3 object
metadata and read back after transfer. Export succeeds only when the remote
metadata matches the local verified archive digest.

A machine-readable export receipt records the durable destination and integrity
result.

The export workflow has read-only access to GitHub release/repository contents
and does not alter published releases or tags.
