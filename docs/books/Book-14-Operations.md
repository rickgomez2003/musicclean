# Book 14 — Operations

0.6.47 adds Recovery SLO Alerting & Escalation.

Recovery SLO status and recovery-duration trend evidence are converted into a
provider-neutral alert record. WARN maps to ADVISORY, FAIL maps to CRITICAL,
and two consecutive failed drills escalate to ESCALATED. A worsening duration
trend can generate an advisory even when the point-in-time SLO has not failed.

A 24-hour suppression-window value is recorded for future delivery-provider
deduplication.

The current implementation publishes only GitHub Actions summary/evidence and
does not require external notification credentials.
