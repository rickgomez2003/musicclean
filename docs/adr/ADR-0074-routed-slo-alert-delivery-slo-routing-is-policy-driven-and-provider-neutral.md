# ADR-0074: Routed SLO Alert Delivery SLO Routing Is Policy-Driven and Provider-Neutral

- **Status:** Accepted
- **Date:** 2026-08-09

Orion 0.6.68 adds logical escalation and routing for routed recovery SLO alert delivery SLO alerts.

NONE routes to `none`, ADVISORY routes to `operations`, and CRITICAL and ESCALATED route to `incident-response` by default. The escalated route remains policy-controlled.

Routing remains provider-neutral, external delivery remains disabled, and generated route evidence remains secret-safe.
