# Book 14 — Operations

0.6.45 adds explicit recovery objectives and SLO evaluation.

Recovery drill evidence is now evaluated against policy for recovery duration,
age of the last successful drill, and successful-drill ratio. Metrics produce
PASS, WARN, or FAIL outcomes, with warning thresholds providing early signal
before a hard objective breach.

The default recovery-time objective is 900 seconds with warning at 720 seconds.
The latest successful drill should be no older than 14 days, with warning after
10 days. Successful-drill ratio must remain at or above 95 percent, with
warning below 98 percent once enough samples exist.

SLO evaluation is read-only and emits machine-readable evidence.
