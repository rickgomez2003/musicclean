# ADR-0046: Release Audit Evidence Is Read-Only and Artifact-Based

- **Status:** Accepted
- **Date:** 2026-08-05

MusicClean collects release audit evidence without changing the release being
audited.

The audit workflow has read-only repository contents permission. It resolves an
existing published release, checks out the exact release tag, downloads the
published assets, verifies checksum coverage, records release/workflow identity,
and uploads a machine-readable evidence bundle as a GitHub Actions artifact.

The evidence process never rebuilds packages, edits release metadata, uploads
new release assets, deletes tags/releases, or creates attestations.

This preserves a clean separation between operational release actions and
evidence collection.
