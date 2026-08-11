# ADR-0078: Routed SLO Alert Delivery Routed Delivery SLOs Are Policy-Driven and Sample-Gated

- **Status:** Accepted
- **Date:** 2026-08-11

Orion 0.6.72 evaluates service-level objectives over routed SLO alert-delivery
routed-delivery observability evidence.

The policy defines thresholds for delivery success rate, retry rate, average
delivery attempts, and transport failure rate. Results are classified as PASS,
WARN, FAIL, or INSUFFICIENT_SAMPLES.

Minimum-sample gating prevents insufficient evidence from producing
authoritative PASS or FAIL classifications.
