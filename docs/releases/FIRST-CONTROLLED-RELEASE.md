# First Controlled Release — 0.6.30

This checklist is intentionally procedural.

## Before merge

- Version source reports `0.6.30`.
- Ruff passes.
- MyPy passes.
- Pytest passes.
- Coverage remains at or above the repository threshold.
- Wheel and source distribution build successfully.
- Twine validates both artifacts.
- SHA256SUMS is generated.
- Release-candidate artifact validation passes.
- Pull-request `Orion Release Candidate` workflow is green.

## After merge to develop

Do not tag from the feature branch.

1. Check out `develop`.
2. Pull `origin/develop`.
3. Confirm the working tree is clean.
4. Confirm `musicclean.__version__` is `0.6.30`.
5. Confirm the merged commit is the intended release commit.
6. Confirm repository release readiness.

Only then create:

`git tag -a v0.6.30 -m "MusicClean 0.6.30"`

Push with:

`git push origin v0.6.30`

The tag triggers the `Orion Release` workflow.

## Verify the GitHub Release

Confirm the release contains:

- `musicclean-0.6.30-py3-none-any.whl`;
- `musicclean-0.6.30.tar.gz`;
- `SHA256SUMS`.

Confirm the release workflow is green.

## Rollback / reissue

Do not move or reuse a published release tag.

If 0.6.30 is defective:

1. document the defect;
2. fix it on a new branch;
3. increment the version;
4. repeat release-candidate validation;
5. publish a new tag.

The prior release remains immutable and auditable.
