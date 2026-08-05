# Archive Restore & Disaster Recovery

The **Orion Archive Restore** workflow restores durable release evidence from
AWS S3 and proves the recovered material is internally consistent.

## Restore inputs

- release tag;
- retention class (`operational` or `long-term`).

The workflow uses the same protected `release-archive-export` GitHub Environment
and GitHub OIDC IAM role as durable export.

## Verification sequence

1. download `release-archive-manifest.json`;
2. download `release-archive.SHA256SUMS`;
3. resolve the archive ZIP from the manifest;
4. read S3 object metadata with `HeadObject`;
5. require remote SHA-256 metadata to match the manifest;
6. download the archive;
7. calculate the downloaded SHA-256 and require an exact match;
8. run the 0.6.41 release archive verifier;
9. safely extract the ZIP with path traversal protection;
10. run the 0.6.40 release audit-evidence verifier;
11. generate and verify a restore receipt.

Restore output is evidence only. The workflow does not recreate a release,
create tags, push refs, promote channels, or alter GitHub Release metadata.
