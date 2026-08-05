# Book 14 — Operations

0.6.39 adds stable-channel rollback and recovery.

A rollback references two already-published releases: the current stable/latest
tag and a previously published recovery tag.

The `release-stable` GitHub Environment protects the operation. The workflow
verifies the request, demotes the current release to prerelease/non-latest,
restores the recovery release to non-prerelease/latest, and verifies final
state.

Rollback preserves artifact and tag identity. Remediation then follows the
normal fix-forward controlled-release process with a new version and tag.
