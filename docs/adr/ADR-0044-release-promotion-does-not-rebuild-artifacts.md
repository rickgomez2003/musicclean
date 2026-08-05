# ADR-0044: Release Promotion Does Not Rebuild Artifacts

- **Status:** Accepted
- **Date:** 2026-08-05

MusicClean separates release creation from release promotion.

A controlled release tag produces one immutable set of release artifacts using
the normal Orion release workflow. Promotion never rebuilds, replaces, or
re-signs those artifacts.

Two channels are defined:

- `preview`: release remains marked as a GitHub prerelease and is not latest;
- `stable`: release is not a prerelease and is marked as GitHub latest.

Promotion is initiated manually with `workflow_dispatch` and references a
GitHub Environment named for the requested channel. Repository owners may add
required reviewers, wait timers, branch/tag restrictions, or other deployment
protection rules to those environments.

Promotion therefore changes release channel metadata, not artifact identity.
