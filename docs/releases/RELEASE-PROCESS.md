# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Prepare a release

1. Update `__version__`.
2. Update release notes/documentation.
3. Run the complete local quality and packaging gate.
4. Merge the release-engineering changes to `develop`.
5. Promote the intended release commit according to repository policy.
6. Create an annotated tag matching the package version, for example:

   `git tag -a v0.6.28 -m "MusicClean 0.6.28"`

7. Push the tag:

   `git push origin v0.6.28`

The `Orion Release` workflow verifies that the tag matches the package version,
runs the quality gate, builds wheel/sdist artifacts, validates metadata,
generates SHA-256 checksums, smoke-tests the built wheel, and creates the GitHub
Release.

A release is never created from a tag whose semantic version disagrees with the
package version.
