# Book 05 — Service Contracts

**Status:** Active specification

## Persistence ports

The first Orion service contracts are repository and Unit-of-Work ports.

### Why ports first

Application behavior should be specified independently from its eventual
persistence implementation.

### Contract style

Ports use Python `Protocol` interfaces. Implementations may be:

- SQLite adapters;
- test in-memory adapters;
- future server/remote adapters where appropriate.

The contracts describe behavior needed by Orion. They are not mirrors of
database tables.
