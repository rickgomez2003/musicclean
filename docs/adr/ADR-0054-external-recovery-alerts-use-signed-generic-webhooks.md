# ADR-0054: External Recovery Alerts Use Signed Generic Webhooks

- **Status:** Accepted
- **Date:** 2026-08-05

External recovery alerts are delivered through a generic HTTPS webhook rather
than coupling recovery policy to a specific SaaS notification provider.

Alert payloads are HMAC-SHA256 signed. The webhook URL and signing secret are
GitHub Environment secrets and are never written into alert artifacts or
delivery receipts.

Delivery is bounded to three attempts with a ten-second request timeout.
Healthy/no-alert records do not make external requests.
