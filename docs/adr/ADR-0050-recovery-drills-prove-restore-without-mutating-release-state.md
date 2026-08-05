# ADR-0050: Recovery Drills Prove Restore Without Mutating Release State

- **Status:** Accepted
- **Date:** 2026-08-05

MusicClean performs recurring recovery drills against a known durable archive.

A drill exercises the same restore trust chain used for disaster recovery:
remote identity verification, archive download, independent archive verification,
re-hash before extraction, safe extraction, and restored evidence validation.

Drills record duration, selected release, retention class, verification result,
and restore receipt in a machine-readable drill record.

A drill never recreates or edits a GitHub Release, creates/pushes tags, changes
promotion state, or modifies the durable archive.
