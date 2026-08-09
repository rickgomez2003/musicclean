# ADR-0073: Routed SLO Alert Delivery SLO Alerting Is Provider-Neutral

- **Status:** Accepted
- **Date:** 2026-08-09

Orion 0.6.67 adds provider-neutral alert generation for routed recovery SLO
alert delivery SLO health and trend evidence. WARN becomes ADVISORY, FAIL
becomes CRITICAL, and authoritative worsening trends can produce ADVISORY
alerts. Consecutive authoritative non-passing observations can escalate the
alert. External delivery remains disabled and evidence remains secret-safe.
