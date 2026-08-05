# Post-Release Verification

The first verification target is `v0.6.30`.

The `Orion Post Release Verification` workflow downloads:

- `musicclean-0.6.30-py3-none-any.whl`
- `musicclean-0.6.30.tar.gz`
- `SHA256SUMS`

It verifies hashes, installs the published wheel into a clean environment,
checks version `0.6.30`, starts Orion, and requires `/v1/health` to return 200.

A failure never causes a published tag to be moved. Corrections use a new
version and a new controlled release.
