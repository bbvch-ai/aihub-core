"""OpenTelemetry configuration settings for SigNoz integration."""

import logging
from typing import Annotated

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings

logger = logging.getLogger(__name__)


class OpenTelemetrySettings(EnvironmentSettings):
    """OpenTelemetry configuration settings with SigNoz integration."""

    model_config = EnvironmentSettings.create_settings_config("OTEL_")

    RESOURCE_SERVICE_NAME: Annotated[str, Field(description="Resource service name")]
    RESOURCE_SERVICE_VERSION: Annotated[str, Field(description="Resource service version")]
    RESOURCE_SERVICE_NAMESPACE: Annotated[str, Field(description="Resource service namespace")]

    EXPORTER_OTLP_ENDPOINT: Annotated[str, Field(description="OTLP exporter endpoint URL")]
    EXPORTER_OTLP_PROTOCOL: Annotated[str, Field(description="OTLP protocol (grpc or http)")] = "grpc"

    def configure_tracing(self) -> TracerProvider | None:
        """Configure OpenTelemetry tracing for SigNoz."""
        # Skip configuration if endpoint or headers are missing
        if not self.EXPORTER_OTLP_ENDPOINT:
            logger.warning("SigNoz tracing not configured: missing endpoint or headers")
            return None

        resource = Resource.create(
            {
                "service.name": self.RESOURCE_SERVICE_NAME,
                "service.version": self.RESOURCE_SERVICE_VERSION,
                "service.namespace": self.RESOURCE_SERVICE_NAMESPACE,
            }
        )

        tracer_provider = TracerProvider(resource=resource)
        otlp_exporter = OTLPSpanExporter(endpoint=self.EXPORTER_OTLP_ENDPOINT, insecure=True)

        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)

        trace.set_tracer_provider(tracer_provider)
        return tracer_provider
