# ADR-0075: Routed SLO Alert Delivery Routed Delivery Uses Route-Specific Signed Webhooks

- **Status:** Accepted
- **Date:** 2026-08-10

Orion 0.6.69 delivers routed recovery SLO alert-delivery alerts through
route-specific HTTPS webhooks.

Operations and incident-response routes use independent step-scoped webhook
URLs and HMAC secrets. Payloads are signed with HMAC-SHA256 and include a
deterministic delivery ID. Route `none` performs no external delivery.

Delivery receipts never persist endpoint URLs, HMAC secrets, signatures,
authorization material, webhook URLs, or request headers.
