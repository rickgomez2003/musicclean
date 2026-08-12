# ADR-0085: Routed SLO Alert Delivery Routed Delivery Routed Delivery SLOs Are Policy-Driven and Sample-Gated

- **Status:** Accepted
- **Date:** 2026-08-11

Orion 0.6.79 adds policy-driven SLO evaluation over routed-delivery observability evidence.

The evaluation covers delivery success rate, retry rate, average attempts, and transport-failure rate. A minimum-sample gate prevents small samples from producing authoritative PASS or FAIL outcomes.

Results use PASS, WARN, FAIL, and INSUFFICIENT_SAMPLES classifications. Evidence remains provider-neutral, secret-safe, and external export remains disabled.
