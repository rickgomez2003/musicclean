# ADR-0066: Routed Recovery Alert Delivery SLO Alerting Is Provider-Neutral

- **Status:** Accepted
- **Date:** 2026-08-08

Orion 0.6.60 converts routed recovery alert delivery SLO and trend evidence into
provider-neutral alert decisions. WARN and FAIL SLO states can generate alerts,
authoritative worsening trends can generate advisory alerts, and consecutive
non-pass history can escalate severity. External delivery remains disabled.
