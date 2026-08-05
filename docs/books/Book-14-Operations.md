# Book 14 — Operations

0.6.40 adds release audit trail and evidence collection.

A manually dispatched read-only workflow resolves an existing published release,
checks out the exact tag, downloads release assets, verifies SHA256SUMS, records
release/workflow identity, confirms the expected wheel/source distribution/SBOM,
and uploads a machine-readable evidence bundle.

Audit evidence collection is separated from release creation, promotion, and
rollback. The evidence workflow cannot edit or replace the audited release.

GitHub Actions retains the generated evidence artifact for 90 days. Export
evidence to an external durable archive when organizational retention
requirements exceed that period.
