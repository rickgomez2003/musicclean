# ADR-0064: Routed Recovery Alert Delivery SLOs Are Policy-Driven and Sample-Gated

- **Status:** Accepted
- **Date:** 2026-08-07

Orion 0.6.58 evaluates routed recovery alert delivery observability against
policy-defined service-level objectives.

The SLO layer evaluates success rate, retry rate, average attempts, average
latency, terminal HTTP failure rate, and transport failure rate. Results are
sample-gated so operators can distinguish authoritative results from
insufficient historical evidence.

SLO evidence remains secret-safe and does not include endpoint URLs, HMAC
material, signatures, authorization material, or webhook destinations.
