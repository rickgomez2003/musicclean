# ADR-0034: Release Engineering Uses One Version Source and Reproducible Artifacts

- **Status:** Accepted
- **Date:** 2026-08-04

MusicClean uses one authoritative version source:

`src/musicclean/version.py`

Package metadata, Orion runtime reporting, release-tag validation, and release
automation derive from that value.

A release tag must match the package version.

Release automation must:

- run the quality gate;
- build wheel and source distributions;
- validate package metadata;
- generate SHA-256 checksums;
- smoke-test the built wheel;
- create the GitHub Release only after those steps succeed.
