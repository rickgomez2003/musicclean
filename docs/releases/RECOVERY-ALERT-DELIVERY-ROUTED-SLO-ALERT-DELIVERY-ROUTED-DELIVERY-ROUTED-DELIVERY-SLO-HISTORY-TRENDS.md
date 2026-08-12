# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery Routed Delivery SLO History & Trends

Orion 0.6.80 adds bounded, deduplicated historical SLO evidence and read-only trend analysis for routed delivery.

The trend layer evaluates delivery success rate, retry rate, average attempts, and transport-failure rate over authoritative SLO observations. It classifies trends as improving, stable, worsening, or insufficient history.

## SLO Alerting in 0.6.81

0.6.81 maps current SLO state and trend evidence into bounded provider-neutral alert classifications while external delivery remains disabled.
