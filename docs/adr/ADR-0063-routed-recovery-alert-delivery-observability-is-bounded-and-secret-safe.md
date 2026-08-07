# ADR-0063: Routed Recovery Alert Delivery Observability Is Bounded and Secret-Safe

- **Status:** Accepted
- **Date:** 2026-08-07

Orion 0.6.57 derives observability from routed-delivery receipts.

Historical receipts are deduplicated by delivery ID and bounded by policy.
Observability includes success rate, retry rate, attempt distribution, route
distribution, failure classes, and latency. Destination URLs, HMAC material,
signatures, authorization material, and other secrets are excluded.
