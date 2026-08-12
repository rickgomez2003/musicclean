# Recovery Alert Delivery Routed SLO Alert Delivery Routed Delivery Routed Delivery SLO Alerting

Orion 0.6.81 adds provider-neutral SLO alert construction over routed-delivery SLO and trend evidence.

The alert layer maps PASS to no alert, WARN to advisory, FAIL to critical, and insufficient evidence to a non-authoritative state. Worsening trends and repeated non-passing observations can increase alert severity. External delivery remains disabled.
