# Book 14 — Operations

0.6.46 adds recovery SLO history and trend analysis.

Recovery Drill workflow artifacts are retrieved using GitHub Actions read-only
permissions. The current drill is combined with prior records, de-duplicated,
chronologically ordered, and bounded to 52 records.

Orion calculates rolling 4-drill and 12-drill success ratios and average
recovery durations. Recovery duration direction is classified as improving,
stable, worsening, or insufficient data.

This allows the 0.6.45 success-ratio SLO to move from bootstrap WARN behavior
toward evidence-backed evaluation as historical samples accumulate.
