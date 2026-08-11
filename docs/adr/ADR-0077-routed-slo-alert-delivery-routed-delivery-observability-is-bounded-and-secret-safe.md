# ADR-0077: Routed SLO Alert Delivery Routed Delivery Observability Is Bounded and Secret-Safe

- **Status:** Accepted
- **Date:** 2026-08-10

Orion 0.6.71 adds observability for resilient routed recovery SLO alert-delivery
delivery.

Observability records terminal outcome, logical route, severity, delivery ID,
attempt and retry counts, terminal HTTP status, failure classification, and a
bounded subset of per-attempt status evidence.

Endpoint URLs, HMAC secrets, signatures, authorization material, webhook URLs,
and request headers are never persisted. External observability export remains
disabled by default.
