# ADR-0015: Knowledge Facts Are Versioned and Traceable to Evidence

- **Status:** Accepted
- **Date:** 2026-08-03

## Decision

A Knowledge fact is an immutable inferred statement that records:

- subject;
- kind and typed value;
- confidence;
- evidence IDs;
- rule ID;
- rule version;
- inference timestamp.

Knowledge is append-oriented. A newer rule version produces new facts instead
of silently rewriting the historical reason a previous conclusion existed.

## First deterministic rules

0.6.9 introduces:

- `metadata.core-complete` v1
- `audio.high-resolution-format` v1

The high-resolution rule is explicitly a technical format classification:
sample rate >= 88.2 kHz OR bit depth >= 24. It is not a claim about audible
quality, mastering quality, or authenticity.
