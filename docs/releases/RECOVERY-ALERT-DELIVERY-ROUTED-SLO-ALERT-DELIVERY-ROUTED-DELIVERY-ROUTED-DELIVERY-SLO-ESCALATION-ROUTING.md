# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery Routed Delivery SLO Escalation & Routing

Orion 0.6.82 adds policy-driven logical routing for routed-delivery SLO alerts.

Non-authoritative and non-alerting evidence routes to `none`; advisory alerts route to `operations`; critical and escalated alerts route to `incident_response`. External delivery remains disabled.

## Routed Delivery in 0.6.83

0.6.83 converts logical operations and incident-response routes into route-specific signed HTTPS webhook delivery while preserving secret-safe receipts.
