# ADR-0045: Release Rollback Restores Channel State Without Mutating Artifacts

- **Status:** Accepted
- **Date:** 2026-08-05

MusicClean rollback restores stable-channel state to a previously published
release rather than rebuilding or replacing release artifacts.

A rollback names the current stable/latest tag and a previously published
recovery tag. The workflow verifies both releases and requires the current tag
to be GitHub's latest release before changing metadata.

The current release is demoted to prerelease/non-latest. The recovery release
is restored to non-prerelease/latest.

Rollback is protected by the `release-stable` GitHub Environment and forbids
artifact rebuilding, release deletion, asset replacement, tag deletion, and
administrative bypass.
