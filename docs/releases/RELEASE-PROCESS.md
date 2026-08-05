# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Dependency maintenance and security

Dependency changes remain subject to security review, runtime auditing, normal
CI, branch protections, and dependency merge policy.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow.

## Controlled release

Controlled releases require an annotated tag matching the authoritative
MusicClean version. Published tags are immutable.

## Recovery operations

Recovery drills exercise durable archive restoration, evaluate recovery SLOs,
analyze historical trends, and generate structured alerts.

0.6.48 delivers required recovery alerts through a signed generic HTTPS
webhook protected by the `release-archive-export` GitHub Environment.
Delivery does not grant repository or release mutation permissions.

## Post-release verification

Post-release verification validates actual published artifacts rather than only
source-tree state.
