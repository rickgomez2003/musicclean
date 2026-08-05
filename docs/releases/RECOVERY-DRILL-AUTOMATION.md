# Recovery Drill Automation

The **Orion Recovery Drill** workflow repeatedly proves that MusicClean can
recover release evidence from durable storage.

The workflow supports manual dispatch and weekly scheduled execution. It
collects bounded historical drill evidence, evaluates recovery SLOs, computes
trends, and now produces structured alert evidence.

Outputs include:

- `recovery-drill.json`
- `recovery-drill-history.json`
- `recovery-slo-report.json`
- `recovery-slo-trend.json`
- `recovery-slo-alert.json`
- `recovery-slo-alert-summary.md`
- restore evidence

Alert generation is provider-neutral in 0.6.47 and does not deliver externally.
