import pytest
from mongoengine import ValidationError

from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_entity import IngestorEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType
from swiss_ai_hub.core.persistence.rag.datalake.entities.source_pipeline import SourcePipeline
from swiss_ai_hub.core.persistence.rag.datalake.entities.source_pipeline_entity import SourcePipelineEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.source_pipeline_type import SourcePipelineType


def _source_pipeline(source_id: str) -> SourcePipeline:
    return SourcePipeline(
        id=source_id,
        display_name=LocaleString(en="Acme Sync"),
        description=LocaleString(en="Acme's custom sync pipeline"),
    )


class TestReservedIds:
    @pytest.mark.parametrize("reserved", [ingestor_type.value for ingestor_type in IngestorType])
    def test_every_ingestor_token_is_reserved_for_source_pipelines(self, reserved):
        """Both kinds of pipeline name their jobs after their token; a shared token would make the single-flight
        guard suppress the other's runs."""
        assert reserved in SourcePipelineEntity.reserved_ids()

    @pytest.mark.parametrize("reserved", [source_type.value for source_type in SourcePipelineType])
    def test_every_source_pipeline_token_is_reserved_for_ingestors(self, reserved):
        assert reserved in IngestorEntity.reserved_ids()

    def test_the_shipped_source_pipeline_id_is_registrable(self):
        assert SourcePipelineType.RCLONE.value not in SourcePipelineEntity.reserved_ids()

    def test_the_legacy_subject_source_type_is_reserved(self):
        assert "datalake" in SourcePipelineEntity.reserved_ids()

    def test_upsert_rejects_a_reserved_id_before_touching_the_database(self):
        with pytest.raises(ValidationError, match="reserved"):
            SourcePipelineEntity.upsert(_source_pipeline(IngestorType.DOCUMENT_INGESTION.value))
