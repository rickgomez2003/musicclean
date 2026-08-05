# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Dependency security gate

Before a change reaches a controlled release, pull-request automation performs
two dependency-security checks:

1. GitHub Dependency Review blocks newly introduced HIGH or CRITICAL
   vulnerabilities in runtime dependency changes.
2. `pip-audit` audits a fresh isolated environment containing the resolved
   MusicClean Orion runtime dependencies.

Vulnerability exceptions must follow
`docs/security/DEPENDENCY-VULNERABILITY-POLICY.md`.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow. Candidate workflows do not publish
production attestations.

## Publish a controlled release

An annotated tag is created only from the exact merged commit that passed
release-candidate validation.

The production release workflow:

1. builds and validates the wheel and source distribution;
2. generates and validates an SPDX JSON SBOM for the wheel;
3. generates SHA256SUMS including the SBOM;
4. smoke-tests the built wheel;
5. creates build-provenance attestations for release assets;
6. creates an SBOM attestation binding the wheel to its SBOM;
7. publishes all assets to the GitHub Release.

Published tags are immutable.

## Post-release verification

Post-release verification downloads actual published release assets, verifies
checksums, installs the published wheel into a clean environment, starts Orion,
and verifies `/v1/health`.

## Stable release operations

Patch and hotfix releases follow the same dependency-security, candidate,
provenance, SBOM, and post-release verification path.
