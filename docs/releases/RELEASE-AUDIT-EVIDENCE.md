# Release Audit Trail & Evidence

The **Orion Release Audit Evidence** workflow produces a machine-readable
evidence bundle for an existing published MusicClean release.

The evidence record includes repository, tag, tag commit, checked-out commit,
actor, workflow/run identity, GitHub Release metadata, release asset names and
sizes, calculated SHA-256 digests, declared checksum matches, and presence of
the expected wheel, source distribution, SHA256SUMS, and SPDX SBOM.

The workflow is intentionally read-only with respect to the release. It does
not build, edit, upload, delete, promote, or roll back release content.

The evidence bundle contains:

- `release-audit-evidence.json`
- `release-audit-evidence.SHA256SUMS`
- `release-metadata.json`

The GitHub Actions artifact is retained for 90 days. Longer retention should be
implemented by exporting these evidence bundles to the organization's durable
records/archive system rather than mutating historical releases.
