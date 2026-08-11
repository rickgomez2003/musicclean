# ADR-0079: Routed SLO Alert Delivery Routed Delivery SLO History Is Bounded, Deduplicated, and Read-Only

- **Status:** Accepted
- **Date:** 2026-08-11

Orion 0.6.73 adds bounded history and read-only trend analysis for routed SLO
alert-delivery routed-delivery SLO evidence.

History is deduplicated by deterministic delivery ID and capped by policy.
Trend analysis operates only on retained, secret-safe SLO evidence and does
not mutate delivery state, credentials, routes, or external systems.

Trend authority is minimum-sample gated. Metrics may report IMPROVING,
WORSENING, STABLE, or INSUFFICIENT_SAMPLES.
