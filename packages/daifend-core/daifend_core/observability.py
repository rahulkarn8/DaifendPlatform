"""OpenTelemetry bootstrap for FastAPI services (OTLP HTTP → Jaeger / collector)."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def instrument_fastapi(app: FastAPI, service_name: str) -> None:
    """Trace HTTP requests. If OTEL_EXPORTER_OTLP_ENDPOINT is unset, only the SDK is registered (no export)."""
    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create(
        {
            "service.name": service_name,
            "deployment.environment": os.getenv("DAIFEND_ENV", "development"),
        }
    )
    provider = TracerProvider(resource=resource)
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        base = endpoint.rstrip("/")
        url = base if base.endswith("/v1/traces") else f"{base}/v1/traces"
        exporter = OTLPSpanExporter(endpoint=url)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info("OpenTelemetry OTLP traces → %s", url)
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor().instrument_app(app)


def instrument_httpx() -> None:
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except Exception as exc:  # pragma: no cover
        logger.debug("httpx instrumentation skipped: %s", exc)
