# Recovery Alert Delivery Routed Delivery

Orion 0.6.55 adds route-specific external delivery for recovery alert delivery
SLO alerts.

The provider-neutral route decision selects either the operations route or the
incident-response route. Each route uses its own HTTPS webhook URL and HMAC
secret.

The delivery tool emits a secret-safe receipt containing route, severity,
status, elapsed time, deterministic delivery ID, and failure classification.
