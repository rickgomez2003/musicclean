# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow.

## Publish a controlled release

A release tag is created only from the exact merged commit that passed
release-candidate validation.

Example:

`git tag -a v0.6.30 -m "MusicClean 0.6.30"`

`git push origin v0.6.30`

The tag triggers the `Orion Release` workflow and publishes the wheel, source
distribution, and SHA256SUMS. Published tags are immutable.

## Post-release verification

After publication, run `Orion Post Release Verification` against the published
tag. It downloads the actual release assets, verifies checksums, installs the
published wheel into a clean environment, starts Orion, and verifies
`/v1/health`.

Corrections use a new version rather than moving a published tag.
