# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow.

The workflow:

1. verifies source and controlled-release readiness;
2. runs Ruff, MyPy, and Pytest;
3. builds a wheel and source distribution;
4. validates package metadata;
5. generates SHA-256 checksums;
6. validates artifact names and versions;
7. installs the wheel into a clean virtual environment;
8. verifies the installed package version;
9. starts Orion from the installed wheel;
10. requires `/v1/health` to return HTTP 200;
11. uploads candidate artifacts for inspection.

The release-candidate workflow does not publish a GitHub Release.

## Publish a controlled release

A release tag is created only from the exact merged commit that has passed
release-candidate validation.

1. Merge the release preparation PR.
2. Check out and update `develop`.
3. Confirm the working tree is clean.
4. Verify the package version.
5. Verify the intended merged commit.
6. Create an annotated tag matching the package version.
7. Push the tag.

Example:

`git tag -a v0.6.30 -m "MusicClean 0.6.30"`

`git push origin v0.6.30`

The `Orion Release` workflow verifies the tag, reruns the quality gate, builds
wheel/sdist artifacts, validates metadata, generates SHA-256 checksums,
smoke-tests the built wheel, and creates the GitHub Release.

Published tags are not moved or reused. Corrections use a new version.
