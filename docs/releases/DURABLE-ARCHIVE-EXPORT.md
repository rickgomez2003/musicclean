# Durable Archive Export

The **Orion Durable Archive Export** workflow exports an already verified
release archive bundle to AWS S3.

## Authentication

The workflow uses GitHub OIDC with an IAM role supplied through the protected
`release-archive-export` GitHub Environment.

Required configuration:

- secret: `AWS_ARCHIVE_ROLE_ARN`
- variable: `AWS_ARCHIVE_BUCKET`
- optional variable: `AWS_ARCHIVE_PREFIX`

If no prefix is configured, `musicclean/releases` is used.

Do not configure long-lived `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY`
credentials for this workflow.

## Integrity

Before export, the 0.6.41 archive bundle is verified.

The archive ZIP is uploaded with its SHA-256 stored in S3 object metadata.
The workflow performs `HeadObject` after upload and requires the remote metadata
digest to equal the archive manifest digest.

The workflow then generates `durable-export-receipt.json` containing the
provider, bucket, object prefix, release tag, retention class, source/export run
IDs, archive identity, and verified SHA-256.

## IAM scope

The IAM role should be restricted to the configured archive bucket/prefix and
should contain only the object operations needed for archival.

Published GitHub Releases remain read-only.
