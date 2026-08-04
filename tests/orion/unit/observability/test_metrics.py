from musicclean.orion.observability.metrics import RuntimeMetrics


def test_metrics_record_requests_errors_and_duration() -> None:
    metrics = RuntimeMetrics()
    metrics.record_request(200, 10.0)
    metrics.record_request(500, 30.0)
    snapshot = metrics.snapshot()
    assert snapshot["requests_total"] == 2
    assert snapshot["errors_total"] == 1
    assert snapshot["request_duration_ms_average"] == 20.0
