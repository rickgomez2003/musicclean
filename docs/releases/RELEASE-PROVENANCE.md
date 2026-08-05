# Release Provenance & Attestations

MusicClean controlled releases use GitHub artifact attestations in addition to
SHA-256 checksums.

## What is attested

The production release workflow attests:

- the MusicClean wheel;
- the source distribution;
- `SHA256SUMS`.

Attestation happens after the artifacts are built and validated and before the
GitHub Release is published.

## Trust model

A checksum proves that a downloaded file matches a known digest.

An artifact attestation additionally binds that artifact digest to build
provenance, including the repository, commit and GitHub Actions workflow that
produced it.

## Verify a release artifact

With GitHub CLI installed, download a release artifact and verify it against
the repository:

`gh attestation verify PATH_TO_ARTIFACT --repo rickgomez2003/musicclean`

Verify both the wheel and source distribution.

Checksum verification remains required as an independent integrity check.

## Permissions

Only the production release workflow is granted:

- `id-token: write`;
- `attestations: write`;
- `artifact-metadata: write`.

Candidate and ordinary CI workflows do not publish production attestations.
