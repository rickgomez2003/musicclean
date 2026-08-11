# ADR-0083: Routed SLO Alert Delivery Routed Delivery Routed Delivery Retries Are Bounded and Idempotency-Aware

- **Status:** Accepted
- **Date:** 2026-08-11

Orion 0.6.77 adds bounded retry behavior to routed SLO alert-delivery
routed-delivery webhook delivery.

Retries are policy-driven and limited to configured transport failures and HTTP
status codes. Backoff is exponential and capped. The deterministic delivery ID
is preserved across attempts so downstream receivers can apply idempotency
semantics.

Per-attempt evidence is bounded and secret-safe.
