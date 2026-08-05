# ADR-0037: Post-Release Verification Uses Published Artifacts

- **Status:** Accepted
- **Date:** 2026-08-04

Post-release verification downloads and executes the artifacts attached to the
published GitHub Release. Locally rebuilt artifacts are not substitutes.

Verification proves that expected assets exist, SHA256SUMS matches the
published wheel and source distribution, the wheel installs cleanly, the
installed version is correct, Orion starts, and `/v1/health` returns HTTP 200.

Published tags and release artifacts remain immutable.
