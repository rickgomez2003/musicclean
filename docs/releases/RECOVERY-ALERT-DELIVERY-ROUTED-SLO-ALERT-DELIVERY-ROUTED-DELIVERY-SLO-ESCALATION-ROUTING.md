# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery SLO Escalation & Routing

Orion 0.6.75 adds policy-driven logical routing for routed SLO alert-delivery
routed-delivery SLO alert evidence.

The routing layer maps no-alert and non-authoritative states to `none`,
advisories to `operations`, and critical or escalated alerts to
`incident-response`. It emits secret-safe route JSON plus a GitHub Actions
summary while keeping external delivery disabled.

## Routed delivery in 0.6.76

0.6.76 consumes provider-neutral route evidence and performs route-specific, HTTPS-only signed webhook delivery while preserving secret-safe receipts.
