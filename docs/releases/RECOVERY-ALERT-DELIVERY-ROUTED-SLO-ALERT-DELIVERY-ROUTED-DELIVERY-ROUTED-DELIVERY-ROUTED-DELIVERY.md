# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery Routed Delivery Routed Delivery

Orion 0.6.83 adds actual delivery for the logical routes created in 0.6.82.

The `none` route performs no delivery. `operations` and `incident_response` use route-specific HTTPS webhooks with HMAC-SHA256 signing and deterministic delivery IDs. Delivery receipts remain provider-neutral and secret-safe.
