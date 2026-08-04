# ADR-0035: Release Candidates Are Validated From Built Artifacts

- **Status:** Accepted
- **Date:** 2026-08-04

Release-candidate validation must exercise the wheel and source distribution
produced by the build process, not only the editable source checkout.

A release candidate must prove:

- wheel and sdist versions match the intended candidate version;
- wheel metadata reports the intended version;
- the sdist contains the authoritative version source;
- SHA-256 checksums cover both artifacts;
- the wheel installs into a clean virtual environment;
- the installed package reports the intended version;
- the installed Orion runtime starts successfully;
- `/v1/health` returns HTTP 200.

Release-candidate validation never publishes artifacts.
