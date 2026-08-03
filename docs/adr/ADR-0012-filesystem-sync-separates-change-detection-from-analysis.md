# ADR-0012: Separate Filesystem Change Detection from Media Analysis

- **Status:** Accepted
- **Date:** 2026-08-03

Orion synchronization observes filesystem state, compares it with known AudioFile
state, classifies changes, and persists lightweight observations.

It does not perform metadata extraction, hashing, fingerprinting, artwork
processing, or audio analysis.

Implemented in 0.6.6: Discovered, Unchanged, Modified.

Reserved for later, once history/identity evidence exists: Moved, Missing,
Restored.
