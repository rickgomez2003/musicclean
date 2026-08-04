# Book 14 — Operations

0.6.24 adds provider-neutral external telemetry export.

Runtime observability can now export structured, already-redacted events through
a pluggable exporter boundary.

The initial concrete adapter is append-only JSONL. Export failures are isolated
from normal Orion request and runtime processing.
