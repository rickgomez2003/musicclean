"""OpenTelemetry adapter for Orion telemetry events."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from musicclean.orion.observability.telemetry import TelemetryEvent

AttributeValue = str | bool | int | float
SpanEmitter = Callable[[str, dict[str, AttributeValue]], None]


class OpenTelemetryTelemetryExporter:
    """Translate Orion telemetry events into OpenTelemetry spans."""

    def __init__(self, emitter: SpanEmitter) -> None:
        self._emitter = emitter

    def export(self, event: TelemetryEvent) -> None:
        attributes = {key: _attribute_value(value) for key, value in event.fields.items()}
        attributes["orion.event.emitted_at"] = event.emitted_at.isoformat()
        self._emitter(event.name, attributes)


def create_otlp_http_emitter(
    *,
    endpoint: str,
    service_name: str,
    service_version: str,
) -> SpanEmitter:
    """Build an OTLP/HTTP span emitter using lazy optional imports."""
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:
        raise RuntimeError(
            "OpenTelemetry support requires requirements/orion-opentelemetry.txt"
        ) from exc

    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": service_name,
                "service.version": service_version,
            }
        )
    )
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=endpoint),
        )
    )
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer("musicclean.orion")

    def emit(name: str, attributes: dict[str, AttributeValue]) -> None:
        with tracer.start_as_current_span(name) as span:
            for key, value in attributes.items():
                span.set_attribute(key, value)

    return emit


def _attribute_value(value: Any) -> AttributeValue:
    if isinstance(value, (str, bool, int, float)):
        return value
    if value is None:
        return "null"
    return str(value)
