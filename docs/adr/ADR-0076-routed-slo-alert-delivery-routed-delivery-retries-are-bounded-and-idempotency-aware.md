# ADR-0076: Routed SLO Alert Delivery Routed Delivery Retries Are Bounded and Idempotency-Aware

- **Status:** Accepted
- **Date:** 2026-08-10

Orion 0.6.70 adds bounded retry resilience to routed recovery SLO alert-delivery
webhook delivery.

Retry behavior is policy-driven. Only configured HTTP statuses and transport
errors are retried, delays use bounded exponential backoff, and the delivery ID
is preserved across attempts by default so receivers can implement idempotent
processing.

Persisted receipts include bounded attempt metadata but never endpoint URLs,
HMAC secrets, signatures, authorization material, webhook URLs, or request
headers.
