# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow. The workflow derives its candidate version
from the authoritative package version; candidate commands and artifact names
do not require manual version synchronization.

## Publish a controlled release

An annotated tag is created only from the exact merged commit that passed
release-candidate validation. Published tags are immutable.

## Post-release verification

After publication, run `Orion Post Release Verification` against the published
tag. Historical version literals are permitted there because the workflow
intentionally targets an immutable published release.

## Stable release operations

Patch and hotfix releases follow the same candidate, controlled-release, and
post-release verification path. Existing tags are never moved or reused.
