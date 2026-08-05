# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Dependency maintenance

Dependabot proposes scheduled updates for Python packages, GitHub Actions, and
the runtime Dockerfile. Routine version-update pull requests target `develop`
and remain subject to normal branch protections and security gates.

Dependabot automation proposes changes; it does not grant automatic merge
authority.

## Dependency security gate

Before a change reaches a controlled release:

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

The production release workflow builds and validates distribution artifacts,
generates and validates the SPDX SBOM, generates checksums, smoke-tests the
wheel, creates build and SBOM attestations, and publishes the GitHub Release.

Published tags are immutable.

## Post-release verification

Post-release verification validates the actual published artifacts rather than
only source-tree state.

## Stable release operations

Patch and hotfix releases follow the same dependency-maintenance,
dependency-security, candidate, provenance, SBOM, and post-release path.
