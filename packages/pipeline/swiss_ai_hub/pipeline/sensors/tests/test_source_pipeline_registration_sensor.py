from unittest.mock import patch

import pytest
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence import IngestorType, SourcePipelineType

from swiss_ai_hub.pipeline.sensors.source_pipeline_registration_sensor import announced_source_pipeline_sensor
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig

_MODULE = "swiss_ai_hub.pipeline.sensors.source_pipeline_registration_sensor"


def _announced(source: str, display_name: LocaleString | None = None, description: LocaleString | None = None):
    with patch(f"{_MODULE}.source_pipeline_registration_sensor") as registration_sensor:
        announced_source_pipeline_sensor(source, display_name, description, StructuredSyncConfig.as_form())
    [source_pipeline] = registration_sensor.call_args.args
    return source_pipeline


class TestLabels:
    @pytest.mark.parametrize("source", [source_type.value for source_type in SourcePipelineType])
    def test_every_shipped_source_is_announced_with_the_platforms_labels(self, source: str):
        announced = _announced(source)

        assert announced.id == source
        assert announced.display_name == LocaleString.from_i18n_path(f"lib.source_pipelines.{source}.display_name")
        assert announced.description == LocaleString.from_i18n_path(f"lib.source_pipelines.{source}.description")

    def test_the_structured_source_is_called_business_application_sync(self):
        assert _announced(SourcePipelineType.STRUCTURED.value).display_name.en == "Business application sync"

    def test_a_custom_source_keeps_the_labels_it_was_given(self):
        announced = _announced("acme_sync", LocaleString(en="Acme"), LocaleString(en="Acme records"))

        assert announced.display_name.en == "Acme"


class TestGate:
    def test_a_custom_source_without_labels_is_refused(self):
        """It could only be offered as its bare id."""
        with pytest.raises(ValueError, match="display_name"):
            _announced("acme_sync")

    def test_an_ingestor_token_is_refused(self):
        with pytest.raises(ValueError, match="reserved"):
            _announced(IngestorType.DOCUMENT_INGESTION.value)
