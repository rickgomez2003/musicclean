# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery SLO Alerting

Orion 0.6.74 adds provider-neutral alert generation for routed SLO
alert-delivery routed-delivery SLO evidence.

The alerting layer considers authoritative SLO classifications, worsening
trends, and consecutive non-passing history. It emits secret-safe structured
JSON plus a GitHub Actions summary while keeping external delivery disabled.

## Routed-delivery SLO escalation and routing in 0.6.75

0.6.75 maps provider-neutral SLO alert states to logical operations or incident-response routes while preserving non-authoritative suppression.
