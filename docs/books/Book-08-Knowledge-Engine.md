# Book 08 — Knowledge Engine

**Status:** Active foundation

The Knowledge Engine consumes Evidence; it does not call parsers directly.

## Pipeline

```text
Provider / Analyzer
      |
      v
EvidenceRecord
      |
      v
Knowledge Rule
      |
      v
Knowledge Fact
      |
      v
Decision Engine
```

Evidence is observation. Knowledge is inference.

0.6.8 establishes the Evidence side of this boundary with immutable typed values
and explicit provenance.
