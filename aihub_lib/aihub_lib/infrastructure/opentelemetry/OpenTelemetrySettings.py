"""OpenTelemetry configuration settings for SigNoz integration."""

import os
from typing import Annotated

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import Field
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class OpenTelemetrySettings(EnvironmentSettings):
    """OpenTelemetry configuration settings with SigNoz integration."""

    model_config = EnvironmentSettings.create_settings_config("OTEL_")

    RESOURCE_ATTRIBUTES: Annotated[str, Field(description="Service resource attributes")] = "service.name=aihub-service"
    EXPORTER_OTLP_ENDPOINT: Annotated[str, Field(description="OTLP exporter endpoint URL")]
    EXPORTER_OTLP_HEADERS: Annotated[str, Field(description="OTLP exporter headers (e.g., authentication tokens)")]
    EXPORTER_OTLP_PROTOCOL: Annotated[str, Field(description="OTLP protocol (grpc or http)")] = "grpc"

    def configure_tracing(self) -> TracerProvider | None:
        """Configure OpenTelemetry tracing for SigNoz following the official documentation."""
        # Skip configuration if endpoint or headers are missing
        if not self.EXPORTER_OTLP_ENDPOINT or not self.EXPORTER_OTLP_HEADERS:
            print("SigNoz tracing not configured: missing endpoint or headers")
            return None

        # Parse resource attributes (e.g., "service.name=aihub-api,service.version=1.0.0")
        resource_attrs = {}
        if self.RESOURCE_ATTRIBUTES:
            for attr in self.RESOURCE_ATTRIBUTES.split(","):
                if "=" in attr:
                    key, value = attr.strip().split("=", 1)
                    resource_attrs[key] = value

        # Add default service information if not provided
        resource_attrs.setdefault("service.name", "aihub-service")
        resource_attrs.setdefault("service.version", "unknown")

        resource_attrs.setdefault("deployment.environment", os.getenv("ENVIRONMENT", "development"))
        resource_attrs.setdefault("service.instance.id", os.getenv("HOSTNAME", "localhost"))

        # Create resource with service information
        resource = Resource.create(resource_attrs)

        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)

        # Parse headers (e.g., "signoz-ingestion-key=xxx,other-header=yyy")
        headers = {}
        if self.EXPORTER_OTLP_HEADERS:
            for header in self.EXPORTER_OTLP_HEADERS.split(","):
                if "=" in header:
                    key, value = header.strip().split("=", 1)
                    headers[key] = value

        # Create OTLP exporter for SigNoz
        otlp_exporter = OTLPSpanExporter(
            endpoint=self.EXPORTER_OTLP_ENDPOINT,
            headers=headers,
            insecure=False,
        )

        # Create span processor and add to tracer provider
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)

        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)

        PymongoInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()
        RequestsInstrumentor().instrument()

        service_name = resource_attrs.get("service.name", "unknown-service")
        print(f"SigNoz tracing configured for service: {service_name}")
        print(f"Endpoint: {self.EXPORTER_OTLP_ENDPOINT}")
        print(f"Protocol: {self.EXPORTER_OTLP_PROTOCOL}")

        return tracer_provider

    @staticmethod
    def shutdown_tracing() -> None:
        """Shutdown tracing provider and flush remaining spans."""
        try:
            provider = trace.get_tracer_provider()
            if hasattr(provider, "shutdown"):
                provider.shutdown()
                print("Tracing provider shut down successfully")
        except Exception as e:
            print(f"Failed to shutdown tracing provider: {e}")
