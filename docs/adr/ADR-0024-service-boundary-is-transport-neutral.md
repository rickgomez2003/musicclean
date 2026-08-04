# ADR-0024: Service Boundary Is Transport-Neutral

- **Status:** Accepted
- **Date:** 2026-08-03

## Decision

External callers interact with Orion through a stable application service
facade rather than directly invoking repositories, SQLite adapters, or low-level
orchestration functions.

The initial service boundary is transport-neutral.

It exposes request and response models suitable for later adaptation to:

- CLI commands;
- REST endpoints;
- desktop UI operations;
- automation.

Transport concerns such as HTTP status codes, JSON serialization, authentication,
and GUI state do not belong in the service layer.

## Rationale

A single stable service contract prevents future user interfaces from becoming
coupled to persistence and orchestration internals.
