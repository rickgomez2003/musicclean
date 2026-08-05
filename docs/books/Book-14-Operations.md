# Book 14 — Operations

0.6.44 adds automated recovery drills.

Orion can now run the 0.6.43 disaster-recovery trust chain manually or on a
weekly schedule against a known durable archive. The drill verifies the remote
archive identity, downloads and verifies the bundle, verifies before extraction,
re-hashes immediately before extraction, safely restores evidence, and validates
the recovered audit evidence.

Each run produces a machine-readable recovery drill record containing the
selected release, run identity, timestamps, elapsed duration, PASS/FAIL result,
and restore receipt.

The drill remains read-only with respect to GitHub Releases, tags, promotion
state, and durable archive content.
