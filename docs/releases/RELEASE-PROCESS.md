# MusicClean Release Process

MusicClean uses `src/musicclean/version.py` as the authoritative version source.

## Dependency maintenance and security

Dependabot updates remain subject to Dependency Review, runtime `pip-audit`,
normal CI, branch protections, and the automated dependency merge policy.

## Release-candidate validation

Before creating a release tag, the intended release commit must pass the
`Orion Release Candidate` workflow.

## Controlled release

Controlled releases require an annotated tag matching the authoritative
MusicClean version.

The production release workflow builds and validates artifacts, generates
checksums and the SPDX SBOM, smoke-tests the wheel, creates provenance/SBOM
attestations, and publishes the GitHub Release.

Published tags are immutable.

## Promotion, rollback, evidence, archival, export, and restore

Promotion and rollback modify channel metadata only. Audit evidence is
read-only. Verified evidence can be archived, exported to durable S3 storage,
and restored through the verified disaster-recovery path.

## Recovery drill automation

`Orion Recovery Drill` exercises the archive restore path manually and on a
weekly schedule.

A known durable archive is selected, restored, verified before extraction,
safely extracted, and validated. The workflow records elapsed duration and
PASS/FAIL evidence in a machine-readable recovery drill record.

Recovery drills never publish releases, create/push tags, modify promotion
state, or change durable archive objects.

## Post-release verification

Post-release verification validates actual published artifacts rather than only
source-tree state.
