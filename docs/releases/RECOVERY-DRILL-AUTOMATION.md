# Recovery Drill Automation

The **Orion Recovery Drill** workflow repeatedly proves that MusicClean can
recover release evidence from durable storage.

The workflow supports manual dispatch and weekly scheduled execution.

0.6.46 retrieves prior Recovery Drill artifacts with read-only Actions access,
builds bounded history, evaluates recovery SLOs against real cross-run samples,
and generates rolling trend evidence.

Outputs include:

- `recovery-drill.json`
- `recovery-drill-history.json`
- `recovery-slo-report.json`
- `recovery-slo-trend.json`
- restore evidence

Recovery drills, history collection, and SLO analysis remain read-only with
respect to releases, tags, promotion state, and durable archive objects.
