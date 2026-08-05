# ADR-0053: Recovery Alerting Is Provider-Neutral Before External Delivery

- **Status:** Accepted
- **Date:** 2026-08-05

Recovery SLO alerting first produces a provider-neutral machine-readable alert
record and GitHub Actions summary.

External delivery providers are intentionally deferred. This avoids coupling
recovery policy to Slack, Teams, PagerDuty, email, or webhook credentials
before the alert schema, severity rules, escalation behavior, and suppression
metadata are stable.

Alert evaluation remains read-only with respect to releases, tags, promotion
state, and durable archives.
