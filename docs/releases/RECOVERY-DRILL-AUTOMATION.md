# Recovery Drill Automation

The **Orion Recovery Drill** workflow repeatedly proves that MusicClean can
recover release evidence from durable storage.

## Schedule

The workflow supports:

- manual dispatch;
- weekly scheduled execution.

Scheduled drills use:

- `RECOVERY_DRILL_TAG`
- `RECOVERY_DRILL_RETENTION_CLASS`

Manual workflow inputs may override those values.

## Drill result

Every drill produces `recovery-drill.json` with:

- drill ID;
- repository and workflow run ID;
- selected release tag;
- retention class;
- start/completion timestamps;
- elapsed seconds;
- PASS or FAIL status;
- restore receipt for passing drills;
- failure reason for failed drills.

A passing drill requires remote verification, download verification, safe
extraction, and restored evidence validation to succeed.

Recovery drills are evidence-only and do not mutate release state.
