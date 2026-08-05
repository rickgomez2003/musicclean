# External Recovery Alert Delivery

External recovery alerts use a generic HTTPS webhook with HMAC-SHA256 signing.

Beginning with 0.6.49, delivery runs in a separate `external-alert-delivery`
job using the protected `recovery-alert-delivery` GitHub Environment.

Required environment secrets:
- `RECOVERY_ALERT_WEBHOOK_URL`
- `RECOVERY_ALERT_WEBHOOK_HMAC_SECRET`

The delivery job does not receive AWS OIDC permissions.

Retry behavior is limited to transient failures, and every delivery carries a
deterministic idempotency/correlation identifier.
