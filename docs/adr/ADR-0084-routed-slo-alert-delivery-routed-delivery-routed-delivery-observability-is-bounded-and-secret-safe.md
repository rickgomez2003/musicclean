# ADR-0084: Routed SLO Alert Delivery Routed Delivery Routed Delivery Observability Is Bounded and Secret-Safe

- **Status:** Accepted
- **Date:** 2026-08-11

Orion 0.6.78 adds bounded, provider-neutral, secret-safe observability over resilient routed-delivery receipts.

The report summarizes terminal delivery state, logical route, attempt count, retry count, terminal HTTP status, failure classification, transport-failure state, retry presence, and bounded attempt evidence.

Endpoint URLs, HMAC secrets, signatures, authorization material, webhook URLs, and request headers are not retained. External export remains disabled.
