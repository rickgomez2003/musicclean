# Release Retention & Archival

The **Orion Release Archive** workflow packages previously verified release
audit evidence into a deterministic archive suitable for durable retention.

Inputs are:

- release tag;
- audit-evidence workflow run ID;
- retention class: `operational` or `long-term`.

The workflow downloads the exact audit-evidence artifact, verifies it, builds a
deterministic ZIP, writes a SHA-256 checksum file, creates an archive manifest,
and uploads the resulting bundle.

Retention policy:

- operational: minimum 90 days;
- long-term: minimum 2555 days (approximately seven years).

GitHub Actions artifact retention remains 90 days in this milestone. Therefore,
`long-term` means the resulting bundle must be exported to durable external
storage before the Actions artifact expires.

No external storage credentials or provider-specific implementation are added
in 0.6.41.
