"""Tests for the OpenTelemetry setup."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import ProxyTracerProvider

from attendflow.telemetry import configure_telemetry, instrument_fastapi


def test_configure_telemetry_is_noop_when_sdk_disabled(monkeypatch):
    monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
    configure_telemetry()
    assert isinstance(trace.get_tracer_provider(), ProxyTracerProvider)


def test_health_probes_are_not_traced_but_api_routes_are(monkeypatch):
    # The SDK turns sampling off when OTEL_SDK_DISABLED is set, and conftest sets it.
    monkeypatch.delenv("OTEL_SDK_DISABLED", raising=False)
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    app = FastAPI()

    @app.get("/health/live")
    def live():
        return {"status": "ok"}

    @app.get("/api/ping")
    def ping():
        return {"pong": True}

    instrument_fastapi(app, tracer_provider=provider)
    client = TestClient(app)
    client.get("/health/live")
    client.get("/api/ping")

    routes = {span.attributes.get("http.route") for span in exporter.get_finished_spans()}
    assert "/api/ping" in routes
    assert "/health/live" not in routes
