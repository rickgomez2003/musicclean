# Recovery Alert Delivery Routed SLO Alert Delivery SLO Escalation & Routing

Orion 0.6.68 adds policy-driven logical routing for routed SLO alert delivery SLO alerts.

Alert severity is converted into explicit logical routes while external delivery remains disabled. Routing evidence remains provider-neutral and secret-safe.

## Routed delivery in 0.6.69

0.6.69 turns the provider-neutral logical route into route-specific signed webhook delivery while preserving secret isolation.
