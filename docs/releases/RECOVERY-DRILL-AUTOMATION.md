# Recovery Drill Automation

The **Orion Recovery Drill** workflow proves durable archive recovery,
evaluates SLOs, computes historical trends, generates alerts, and delivers
required alerts externally.

Outputs include recovery drill, history, SLO, trend, alert, delivery-receipt,
and restore evidence.

External delivery is protected by the `release-archive-export` GitHub
Environment. The workflow remains read-only with respect to repository and
published release state.
