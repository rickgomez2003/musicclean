# Recovery Alert Delivery Routed SLO Alert Delivery

Orion 0.6.62 connects routed-delivery SLO route decisions to route-specific
external delivery.

Operations and incident-response destinations use separate HTTPS endpoints and
separate HMAC secrets. Payloads are signed with HMAC-SHA256, delivery IDs are
deterministic, and only secret-safe receipt evidence is retained.
