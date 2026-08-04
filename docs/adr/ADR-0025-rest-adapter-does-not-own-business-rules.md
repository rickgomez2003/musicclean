# ADR-0025: REST Adapter Does Not Own Business Rules

- **Status:** Accepted
- **Date:** 2026-08-04

The REST adapter owns routing, validation, serialization, and HTTP status
mapping. Execution, reconciliation, lease, idempotency, persistence, and
filesystem rules remain behind `OrionService`.
