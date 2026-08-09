# Recovery Alert Delivery Routed SLO Alert Delivery SLO Alerting

Orion 0.6.67 adds provider-neutral alert generation for routed SLO alert
delivery SLO and authoritative trend evidence.

Alerts use NONE, ADVISORY, CRITICAL, and ESCALATED severities. External
delivery remains disabled until later routing and delivery milestones.

## Escalation and routing in 0.6.68

0.6.68 converts routed SLO delivery alert severity into policy-driven logical routes while preserving provider neutrality.
