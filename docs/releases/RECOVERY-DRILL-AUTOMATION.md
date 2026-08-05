# Recovery Drill Automation

The **Orion Recovery Drill** workflow repeatedly proves that MusicClean can
recover release evidence from durable storage.

## Schedule

The workflow supports manual dispatch and weekly scheduled execution.

Scheduled drills use `RECOVERY_DRILL_TAG` and
`RECOVERY_DRILL_RETENTION_CLASS`. Manual inputs may override them.

## Drill result

Every drill produces `recovery-drill.json` with the selected release, run
identity, timestamps, elapsed seconds, PASS/FAIL status, restore receipt, and
failure reason when applicable.

0.6.45 additionally evaluates passing drill evidence against recovery
objectives and writes `recovery-slo-report.json`.

Recovery drills and SLO evaluation remain read-only and do not mutate release,
tag, promotion, or durable archive state.
