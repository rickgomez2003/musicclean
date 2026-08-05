# Book 14 — Operations

0.6.33 adds release provenance and GitHub artifact attestations.

Controlled release artifacts retain SHA-256 checksum validation and additionally
receive signed build provenance. Checksums establish byte integrity; provenance
establishes the repository, commit and workflow identity associated with the
artifact build.

Only the production release workflow receives attestation-writing permissions.
Release Candidate and ordinary CI workflows do not publish production
attestations.

Operators verify published artifacts with GitHub CLI attestation verification
in addition to SHA256SUMS.
