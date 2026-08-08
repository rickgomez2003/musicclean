# ADR-0070: Routed SLO Alert Delivery Observability Is Bounded and Secret-Safe

- **Status:** Accepted
- **Date:** 2026-08-08

Orion 0.6.64 adds bounded, secret-safe observability evidence for routed recovery
SLO alert delivery. Attempt status history is bounded by policy and external
export remains disabled. Endpoint URLs, HMAC secrets, signatures, authorization
data, webhook URLs, and request headers are forbidden from evidence.
