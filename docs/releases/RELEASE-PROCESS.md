# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow.

The workflow:

1. runs Ruff, MyPy, and Pytest;
2. builds a wheel and source distribution;
3. validates package metadata;
4. generates SHA-256 checksums;
5. validates artifact names and versions;
6. installs the wheel into a clean virtual environment;
7. verifies the installed package version;
8. starts Orion from the installed wheel;
9. requires `/v1/health` to return HTTP 200;
10. uploads the candidate artifacts for inspection.

The release-candidate workflow does not publish a GitHub Release.

## Publish a release

After the release candidate passes:

1. Confirm `src/musicclean/version.py` contains the intended release version.
2. Confirm the release-candidate workflow is green on the merged release commit.
3. Create an annotated tag matching the package version, for example:

   `git tag -a v0.6.29 -m "MusicClean 0.6.29"`

4. Push the tag:

   `git push origin v0.6.29`

The `Orion Release` workflow verifies the tag, reruns the quality gate, builds
wheel/sdist artifacts, validates metadata, generates SHA-256 checksums,
smoke-tests the built wheel, and creates the GitHub Release.
