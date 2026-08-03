# ADR-0005: Keep the Orion Shared Kernel Small

- **Status:** Accepted
- **Date:** 2026-08-03

## Context

Cross-cutting primitives are useful, but a broad shared package can become a dependency dumping ground.

## Decision

The Shared Kernel contains only stable concepts used across multiple Orion bounded contexts:

- stable internal identifiers
- UTC clock abstraction
- base domain events
- foundational error hierarchy
- primitive value objects with domain invariants

General-purpose helpers, filesystem utilities, provider-specific types, database types, and application services do not belong in the Shared Kernel.

## Consequences

The package remains intentionally boring, small, and difficult to change. New additions require evidence that they are truly cross-domain and stable.
