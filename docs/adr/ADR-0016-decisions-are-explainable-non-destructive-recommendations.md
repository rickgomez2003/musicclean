# ADR-0016: Decisions Are Explainable, Non-Destructive Recommendations

- **Status:** Accepted
- **Date:** 2026-08-03

## Decision

A Decision is an immutable recommendation derived from Knowledge.

Every Decision records:

- subject;
- action;
- confidence;
- rationale;
- supporting Knowledge IDs;
- rule ID and version;
- timestamp;
- optional risk statement.

Decision generation never performs filesystem or metadata mutations.

## Initial actions

- KEEP
- REVIEW
- REPAIR_METADATA
- REANALYZE
- IGNORE

Destructive actions such as DELETE are intentionally absent from the initial
DecisionAction vocabulary.

Execution, authorization, quarantine, undo, and destructive operations belong
to later application workflows with explicit safety controls.
