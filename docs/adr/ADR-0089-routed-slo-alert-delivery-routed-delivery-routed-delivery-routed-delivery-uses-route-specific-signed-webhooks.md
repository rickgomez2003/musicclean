# ADR-0089: Routed SLO Alert Delivery Routed Delivery Routed Delivery Routed Delivery Uses Route-Specific Signed Webhooks

- **Status:** Accepted
- **Date:** 2026-08-14

Orion 0.6.83 adds the delivery layer for logical routed-delivery SLO alert routes.

The `none` route performs no delivery. The `operations` and `incident_response` routes use route-specific webhook URLs and HMAC secrets supplied at runtime. Delivery requires HTTPS and signs the canonical JSON payload with HMAC-SHA256.

Delivery IDs are deterministic for the route and canonical payload. Receipts remain secret-safe and do not persist endpoint URLs, credentials, signatures, authorization material, or request headers.
