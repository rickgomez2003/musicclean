# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery Routed Delivery

Orion 0.6.76 adds route-specific, HTTPS-only signed webhook delivery for
routed SLO alert-delivery routed-delivery route evidence.

Operations and incident-response routes use separate credentials.
Payloads use deterministic delivery IDs and HMAC-SHA256 signatures.
The `none` route performs no delivery. Receipts remain secret-safe.

## Routed-delivery resilience in 0.6.77

0.6.77 adds bounded retries for configured HTTP and transport failures while preserving deterministic delivery IDs across attempts.
