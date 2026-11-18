"""OpenTelemetry setup for traces, metrics and logs.

All three signals are sent over OTLP/gRPC to the OpenTelemetry Collector.
The endpoint comes from OTEL_EXPORTER_OTLP_ENDPOINT and the service name from
OTEL_SERVICE_NAME. Set OTEL_SDK_DISABLED=true to turn telemetry off.

configure_telemetry() must run before attendflow.database is imported, so that
the SQLAlchemy instrumentation patches create_engine before the engine is built.
"""

import logging
import os

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from attendflow.config import settings

# Health probes are polled every few seconds; tracing them only adds noise.
EXCLUDED_URLS = "health/live,health/ready"

LOG_FORMAT = (
    "%(asctime)s %(levelname)s %(name)s "
    "trace_id=%(otelTraceID)s span_id=%(otelSpanID)s %(message)s"
)


class _TraceContextDefaults(logging.Filter):
    """Fill trace fields for records created before the log instrumentor was active.

    Without this, the console formatter raises KeyError on those records.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.otelTraceID = getattr(record, "otelTraceID", "0")
        record.otelSpanID = getattr(record, "otelSpanID", "0")
        return True


def _telemetry_disabled() -> bool:
    return os.getenv("OTEL_SDK_DISABLED", "false").strip().lower() == "true"


def instrument_fastapi(app: FastAPI, tracer_provider: TracerProvider | None = None) -> None:
    """Trace HTTP requests for one app instance, skipping the health probes.

    Instrument the app object itself. The global FastAPIInstrumentor().instrument()
    only affects FastAPI instances created after it runs, and main.py imports
    FastAPI before configure_telemetry() is called.
    """
    if _telemetry_disabled():
        return
    FastAPIInstrumentor.instrument_app(
        app, tracer_provider=tracer_provider, excluded_urls=EXCLUDED_URLS
    )


def configure_telemetry() -> None:
    """Install tracer, meter and logger providers and enable auto-instrumentation."""
    if _telemetry_disabled():
        return

    resource = Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "attendflow-backend"),
            "deployment.environment": settings.app_env,
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter())
    metrics.set_meter_provider(
        MeterProvider(resource=resource, metric_readers=[metric_reader])
    )

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    set_logger_provider(logger_provider)

    # Adds otelTraceID and otelSpanID to every LogRecord so console lines match traces.
    # enable_log_auto_instrumentation=False: the explicit LoggingHandler below exports logs.
    LoggingInstrumentor().instrument(
        set_logging_format=False,
        inject_trace_context=True,
        enable_log_auto_instrumentation=False,
    )

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(LOG_FORMAT))
    console.addFilter(_TraceContextDefaults())
    root.addHandler(console)
    root.addHandler(LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider))

    SQLAlchemyInstrumentor().instrument()
