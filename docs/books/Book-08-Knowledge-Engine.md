# Book 08 — Knowledge Engine

**Status:** Active specification

## Purpose

The Knowledge Engine transforms Evidence into explicit, versioned facts.

```text
Evidence
   |
   v
Deterministic Rule
   |
   v
KnowledgeFact
   |
   v
Decision Engine
```

## KnowledgeFact

Every fact records:

- subject;
- kind;
- typed value;
- confidence;
- supporting Evidence IDs;
- rule ID;
- rule version;
- inference timestamp.

This makes every conclusion reproducible and auditable.

## First rules

### metadata.core-complete v1

True when the latest Title, Artist, and Album observations are all present and
nonblank. False when some are missing but at least one relevant observation
exists.

### audio.high-resolution-format v1

A technical format classification only:

- sample rate >= 88.2 kHz, or
- bit depth >= 24.

This rule intentionally does not imply improved sound quality, better mastering,
or genuine high-resolution source provenance.

## Latest evidence

Rules use the newest observation of each relevant EvidenceKind based on the
Evidence provenance timestamp.

## History

Knowledge persistence is append-oriented. Rule upgrades create new facts with a
new rule version so historical conclusions remain explainable.
