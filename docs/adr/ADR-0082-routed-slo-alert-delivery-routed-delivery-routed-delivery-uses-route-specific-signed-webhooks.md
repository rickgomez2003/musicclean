# ADR-0082: Routed SLO Alert Delivery Routed Delivery Routed Delivery Uses Route-Specific Signed Webhooks

- **Status:** Accepted
- **Date:** 2026-08-11

Orion 0.6.76 adds route-specific webhook delivery for routed SLO
alert-delivery routed-delivery route evidence.

The `none` route never delivers. `operations` and `incident-response`
use separate endpoint and HMAC secret inputs. Endpoints must use HTTPS.
Payloads are signed with HMAC-SHA256 and include deterministic delivery IDs.

Delivery receipts are intentionally secret-safe and exclude endpoint URLs,
HMAC secrets, signatures, authorization material, webhook URLs, and request
headers.
