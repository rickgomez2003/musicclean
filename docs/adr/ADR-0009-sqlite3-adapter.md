# ADR-0009: Implement the Initial Orion Persistence Adapter with sqlite3

- **Status:** Accepted
- **Date:** 2026-08-03

## Context

Orion needs a concrete persistence adapter, but the current domain model and
queries are small and explicit. Introducing an ORM now would add mapping and
lifecycle behavior before Orion has demonstrated a need for it.

## Decision

The initial SQLite adapter uses Python's standard-library `sqlite3` module
behind repository ports and the UnitOfWork port.

The domain and application layers remain unaware of this choice.

## Consequences

### Positive

- zero new runtime dependency;
- transparent SQL and transaction behavior;
- easy performance inspection;
- no ORM entities leaking into the domain;
- simple migration path because adapter replacement remains possible.

### Tradeoffs

- SQL and row mapping are explicit;
- more adapter code than a full ORM may require;
- schema evolution remains our responsibility.

This ADR does not prohibit adopting SQLAlchemy later if demonstrated
requirements justify it.
