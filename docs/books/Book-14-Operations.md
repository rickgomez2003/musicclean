# Book 14 â€” Operations

0.6.48 adds External Recovery Alert Delivery.

Recovery alerts are delivered through a generic HTTPS webhook. Required alert
payloads are HMAC-SHA256 signed. Healthy/no-alert results generate no external
request.

Delivery uses the protected `release-archive-export` GitHub Environment with
two secrets: `RECOVERY_ALERT_WEBHOOK_URL` and
`RECOVERY_ALERT_WEBHOOK_HMAC_SECRET`.

Delivery is bounded to three attempts and a ten-second request timeout.
Machine-readable receipts intentionally exclude secret values and destination
URLs.
