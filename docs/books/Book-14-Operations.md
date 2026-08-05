# Book 14 — Operations

0.6.31 adds post-release verification of the published `v0.6.30` GitHub Release.

Verification downloads the published wheel, source distribution, and
SHA256SUMS, verifies integrity, installs the wheel into a clean environment,
starts Orion, and verifies `/v1/health`.

Published tags are never moved in response to a verification failure.
