import logging
from unittest.mock import patch

import pytest
from opentelemetry.sdk._logs import LoggingHandler

from swiss_ai_hub.core.infrastructure.opentelemetry import open_telemetry_settings as module
from swiss_ai_hub.core.infrastructure.opentelemetry.open_telemetry_settings import OpenTelemetrySettings

pytestmark = pytest.mark.unit

# What the SDK would use if we passed nothing. Asserting against the literals rather than importing
# them keeps this test honest if an SDK upgrade quietly raises or lowers them.
SDK_DEFAULT_QUEUE_SIZE = 2048
SDK_DEFAULT_EXPORT_BATCH_SIZE = 512


def _settings() -> OpenTelemetrySettings:
    return OpenTelemetrySettings(
        ENABLED=True,
        EXPORTER_OTLP_ENDPOINT="http://localhost:4317",
        EXPORTER_OTLP_PROTOCOL="grpc",
        RESOURCE_SERVICE_NAME="api",
        RESOURCE_SERVICE_VERSION="test",
        RESOURCE_SERVICE_NAMESPACE="swiss-ai-hub",
    )


class TestLogExportIsSizedForBursts:
    """The SDK's defaults drop records once the queue is full and log nothing when they do, so a
    burst reads as a complete log in the backend while records are missing from it. Measured on a
    20k-record burst against a real collector: 17985/20000 delivered with the defaults, 20000/20000
    with these values."""

    def test_batching_is_raised_above_the_sdk_defaults(self):
        settings = _settings()

        assert settings.BLRP_MAX_QUEUE_SIZE > SDK_DEFAULT_QUEUE_SIZE
        assert settings.BLRP_MAX_EXPORT_BATCH_SIZE > SDK_DEFAULT_EXPORT_BATCH_SIZE

    def test_the_queue_absorbs_more_than_one_export_batch(self):
        """A queue that cannot hold several batches drops during the very first export, which is
        what made the batch size matter as much as the queue depth."""
        settings = _settings()

        assert settings.BLRP_MAX_QUEUE_SIZE >= settings.BLRP_MAX_EXPORT_BATCH_SIZE * 4

    def test_configured_values_reach_the_processor(self):
        settings = _settings()
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers[:]

        with patch.object(module, "BatchLogRecordProcessor") as processor:
            settings.configure_logging()

        try:
            _, kwargs = processor.call_args
            assert kwargs["max_queue_size"] == settings.BLRP_MAX_QUEUE_SIZE
            assert kwargs["max_export_batch_size"] == settings.BLRP_MAX_EXPORT_BATCH_SIZE
        finally:
            root_logger.handlers = [h for h in root_logger.handlers if not isinstance(h, LoggingHandler)]
            root_logger.handlers += [h for h in original_handlers if h not in root_logger.handlers]
