# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Dependency maintenance and merge policy

Dependabot proposes scheduled updates for Python packages, GitHub Actions, and
the runtime Dockerfile.

PATCH and MINOR Dependabot version updates targeting `develop` may have GitHub
auto-merge enabled automatically. MAJOR updates remain manual.

Auto-merge does not bypass branch protections. The repository must require the
CI/security checks that define merge readiness.

## Dependency security gate

Before a dependency change can merge:

1. GitHub Dependency Review evaluates introduced vulnerability risk.
2. `pip-audit` audits the resolved MusicClean Orion runtime environment.
3. normal CI and quality checks remain required according to branch policy.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow.

## Controlled release

Controlled releases require an annotated tag matching the authoritative
MusicClean version.

Example:

git tag -a v<version> -m "MusicClean <version>"
git push origin v<version>

The production release path continues to build and validate artifacts, generate
the SPDX SBOM and checksums, smoke-test the wheel, create provenance/SBOM
attestations, publish the GitHub Release, and perform post-release
verification.

Published tags are immutable.
