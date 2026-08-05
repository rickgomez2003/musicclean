# Recovery SLO History & Trend Analysis

Recovery Drill workflow artifacts are read with GitHub Actions read-only
permissions and reduced to a bounded analytical history.

The history is de-duplicated by drill ID, ordered by completion timestamp, and
bounded to 52 records. Rolling 4-drill and 12-drill windows provide success
ratio and recovery-duration evidence.

0.6.47 consumes the point-in-time SLO report and duration trend as inputs to
provider-neutral alerting and escalation.
