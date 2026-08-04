# Book 05 — Service Contracts

**Status:** Active specification

## Orion service boundary

0.6.18 introduces `OrionService`, a transport-neutral facade over application
orchestration.

Initial capabilities:

- health
- coordinated quarantine
- coordinated restore
- reconciliation

The boundary uses explicit request and response objects.

It does not expose:

- SQLite connections
- repositories
- UnitOfWork implementation details
- filesystem adapter implementation details

## Interface layering

```text
CLI / REST / Desktop / Automation
              ↓
         OrionService
              ↓
       Application Layer
              ↓
       Ports / Adapters
```

Future transports should adapt to this service boundary instead of duplicating
business orchestration.
