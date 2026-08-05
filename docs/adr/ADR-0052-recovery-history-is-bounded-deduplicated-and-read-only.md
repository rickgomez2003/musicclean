# ADR-0052: Recovery History Is Bounded, Deduplicated, and Read-Only

- **Status:** Accepted
- **Date:** 2026-08-05

Recovery SLO evaluation consumes prior Recovery Drill artifacts using
read-only GitHub Actions access.

History is bounded to 52 records, de-duplicated by drill ID, and sorted by
completion timestamp. The current drill is always included after prior
artifact collection.

Trend analysis derives rolling success ratios and recovery-duration averages
from this bounded evidence set. No release, tag, promotion, or archive state is
modified while collecting history.
