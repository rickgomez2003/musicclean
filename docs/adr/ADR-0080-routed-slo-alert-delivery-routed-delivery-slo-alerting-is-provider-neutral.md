# ADR-0080: Routed SLO Alert Delivery Routed Delivery SLO Alerting Is Provider-Neutral

- **Status:** Accepted
- **Date:** 2026-08-11

Orion 0.6.74 adds provider-neutral alert generation from routed SLO
alert-delivery routed-delivery SLO and trend evidence.

Authoritative WARN and FAIL results may create advisory or critical alerts.
Authoritative worsening trends may also create advisory alerts. Insufficient
samples never create authoritative alerts.

Repeated authoritative non-passing observations may escalate severity after a
policy-defined threshold. This layer does not perform external delivery.
