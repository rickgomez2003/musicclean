# Recovery Alert Delivery Routed Delivery Observability

Orion 0.6.57 adds secret-safe observability for routed recovery alert delivery.

The observability artifact aggregates current and bounded historical routed
delivery receipts into delivery success rate, retry rate, attempt statistics,
route distribution, failure-class counts, and latency statistics.

A Markdown summary is published to the recovery drill job summary and both
artifacts are retained with recovery drill evidence.
