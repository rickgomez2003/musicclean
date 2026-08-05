# ADR-0051: Recovery Objectives Are Evaluated From Drill Evidence

- **Status:** Accepted
- **Date:** 2026-08-05

MusicClean recovery objectives are evaluated from machine-readable recovery
drill evidence rather than inferred from workflow success alone.

The initial policy evaluates:

- recovery duration;
- age of the latest successful drill;
- successful-drill ratio over a minimum sample window.

Metrics produce PASS, WARN, or FAIL states. Warning thresholds provide early
signal before a hard objective breach.

Recovery SLO evaluation is read-only and never mutates release, archive,
promotion, or recovery state.
