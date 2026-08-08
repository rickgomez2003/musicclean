# Recovery Alert Delivery Routed SLO Alert Delivery SLOs

Orion 0.6.65 adds policy-driven, sample-gated SLO evaluation to routed recovery
SLO alert delivery observability.

The SLOs cover delivery success, retry rate, average attempts, and transport
failure rate. Insufficient sample counts produce non-authoritative evidence
instead of false PASS/FAIL classifications.
