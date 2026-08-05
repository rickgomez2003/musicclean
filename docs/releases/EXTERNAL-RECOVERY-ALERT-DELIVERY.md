# External Recovery Alert Delivery

Orion 0.6.48 delivers provider-neutral recovery alerts to a generic HTTPS
webhook.

## GitHub Environment

Configure the protected environment:

`recovery-alert-delivery`

Required secrets:

- `RECOVERY_ALERT_WEBHOOK_URL`
- `RECOVERY_ALERT_WEBHOOK_HMAC_SECRET`

The URL must use HTTPS.

## Delivery behavior

- healthy/no-alert records are not sent;
- required alerts are POSTed as JSON;
- payloads are HMAC-SHA256 signed;
- maximum delivery attempts: 3;
- request timeout: 10 seconds;
- failed delivery causes the delivery step to fail;
- delivery metadata is recorded in `recovery-alert-delivery.json`;
- secret material is never included in the receipt.

Receivers can validate the `X-MusicClean-Signature-SHA256` header against the
exact request body.
