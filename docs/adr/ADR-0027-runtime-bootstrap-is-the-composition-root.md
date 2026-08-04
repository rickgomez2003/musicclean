# ADR-0027: Runtime Bootstrap Is the Composition Root

- **Status:** Accepted
- **Date:** 2026-08-04

## Decision

Concrete infrastructure assembly occurs in `musicclean.orion.runtime`.

The runtime layer is responsible for constructing:

- SQLite persistence;
- migrations;
- filesystem mutation adapter;
- production clock;
- UnitOfWork factory;
- `OrionService`;
- FastAPI host;
- startup reconciliation;
- Uvicorn process launch.

Domain and application layers do not construct concrete adapters.

## Safe defaults

The HTTP listener defaults to `127.0.0.1:8765`.

Startup reconciliation is enabled by default and remains detection-only.

Network exposure beyond localhost requires explicit configuration.
