# ADR-0068: Routed SLO Alert Delivery Uses Route-Specific Signed Webhooks

- **Status:** Accepted
- **Date:** 2026-08-08

Orion 0.6.62 introduces external delivery for routed recovery alert delivery
SLO alerts.

Operations and incident-response routes use separate HTTPS webhook URLs and
separate HMAC secrets. Payloads are canonical JSON signed with HMAC-SHA256.
Delivery receipts are secret-safe and do not persist endpoint URLs, HMAC
secrets, signatures, authorization material, or request headers.

Credentials remain scoped to the delivery step and are never persisted through
GITHUB_ENV.
