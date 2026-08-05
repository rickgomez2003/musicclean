# ADR-0047: Release Archives Are Deterministic and Provider-Neutral

- **Status:** Accepted
- **Date:** 2026-08-05

MusicClean packages verified release evidence into deterministic archive bundles
before any long-term external retention integration.

The archive format is provider-neutral. GitHub Actions can temporarily retain
the bundle, while organizational policy may later copy the exact archive and
checksum to durable object storage or records-management systems.

Long-term retention does not modify GitHub Releases, release tags, or original
audit evidence.
