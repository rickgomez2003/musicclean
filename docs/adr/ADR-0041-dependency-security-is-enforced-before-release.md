# ADR-0041: Dependency Security Is Enforced Before Release

- **Status:** Accepted
- **Date:** 2026-08-04

MusicClean evaluates dependency vulnerability risk before code reaches a
controlled release.

Pull requests use GitHub Dependency Review to reject newly introduced HIGH or
CRITICAL vulnerabilities in runtime dependency changes.

A separate isolated Python environment installs Orion runtime dependencies and
uses `pip-audit` to check the fully resolved environment against current
vulnerability data.

These controls complement the release SBOM:

- the SBOM records what is present;
- dependency review prevents known vulnerable dependency changes;
- pip-audit evaluates the currently resolved runtime environment.

Exceptions are exceptional, explicit, owned, justified, and limited to no more
than 30 days. The repository starts with no vulnerability exceptions.
