# Book 09 — Decision Engine

**Status:** Active specification

## Purpose

The Decision Engine transforms Knowledge into explicit, explainable
recommendations.

```text
Evidence
   ↓
Knowledge
   ↓
Decision
   ↓
Future Review / Authorization / Execution
```

## Safety boundary

A Decision is not an execution request.

0.6.10 deliberately excludes DELETE or other destructive actions. The initial
actions are:

- KEEP
- REVIEW
- REPAIR_METADATA
- REANALYZE
- IGNORE

## Traceability

Every Decision records its supporting Knowledge IDs and rule version. Each
KnowledgeFact already links to Evidence IDs, producing a complete explanation
chain:

```text
Decision
  └── KnowledgeFact
        └── EvidenceRecord
              └── provider + timestamp + warning
```

## First rules

### decision.metadata-repair v1

- core metadata incomplete -> REPAIR_METADATA
- core metadata complete -> KEEP

### decision.high-resolution-review v1

A technically high-resolution format -> REVIEW.

The recommendation does not claim better sound or genuine high-resolution
provenance. Future spectral/provenance analysis may refine it.

## Future execution model

Execution will be a separate application boundary requiring explicit
authorization, safeguards, audit history, and undo/quarantine where applicable.
