# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery

Orion 0.6.69 adds route-specific signed webhook delivery for routed recovery
SLO alert-delivery alerts.

Operations and incident-response routes use separate credentials. HTTPS is
required, payloads are HMAC-SHA256 signed, delivery IDs are deterministic, and
delivery receipts remain secret-safe.
