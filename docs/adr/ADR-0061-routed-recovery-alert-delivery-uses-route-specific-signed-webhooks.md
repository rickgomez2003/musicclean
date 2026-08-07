# ADR-0061: Routed Recovery Alert Delivery Uses Route-Specific Signed Webhooks

- **Status:** Accepted
- **Date:** 2026-08-07

0.6.55 performs external delivery from the provider-neutral route decision.

Operations and incident-response routes use separate HTTPS endpoints and
separate HMAC secrets. Payloads are signed, route-aware, and identified by a
deterministic delivery ID. Delivery receipts contain no secret material.
