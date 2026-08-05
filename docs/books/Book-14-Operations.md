# Book 14 — Operations

0.6.35 adds dependency and vulnerability policy enforcement.

Pull requests use GitHub Dependency Review to block newly introduced HIGH or
CRITICAL vulnerabilities in runtime dependencies. A separate isolated Python
environment installs the Orion runtime dependency set and audits it with
`pip-audit`.

The operational supply-chain controls are now layered:

- SHA-256 checksums: byte integrity;
- build provenance: repository, commit, and workflow identity;
- SPDX SBOM: component inventory;
- Dependency Review: vulnerable dependency changes before merge;
- pip-audit: known vulnerabilities in the resolved runtime environment.

Vulnerability exceptions must be explicit, owned, justified, and time-bounded.
