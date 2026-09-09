"""Per-run resolution of a knowledge database's configuration over the deployment defaults."""

from typing import Annotated
from unittest.mock import Mock, patch

import pytest
from pydantic import Field
from swiss_ai_hub.core.infrastructure import DocumentIngestionPipelineSettings
from swiss_ai_hub.core.persistence import LocaleStringEntity

from swiss_ai_hub.pipeline.ingestors.document_ingestion_config import DocumentIngestionConfig
from swiss_ai_hub.pipeline.util import model_builders

_MODULE = "swiss_ai_hub.pipeline.util.model_builders"


def _bucket(configuration: dict | None) -> Mock:
    bucket = Mock()
    bucket.configuration = configuration or {}
    bucket.name = LocaleStringEntity(en="Contracts")
    bucket.description = LocaleStringEntity(en="Signed contracts")
    return bucket


@pytest.fixture
def deployment_defaults():
    settings = DocumentIngestionPipelineSettings(
        LLM_MODEL="text-generation/default-llm",
        EMBEDDING_MODEL="embedding/default",
        VISION_MODEL=None,
        WITH_SUMMARY_NODES=True,
        WITH_TABLE_REFINEMENT=True,
        WITH_FIGURE_DESCRIPTIONS=False,
    )
    with patch(f"{_MODULE}.DocumentIngestionPipelineSettings", return_value=settings):
        yield settings


class TestIngestorConfigForBucket:
    def test_a_database_without_stored_values_follows_the_deployment_defaults(self, deployment_defaults):
        """Rows created before a knob existed keep ingesting exactly as before."""
        with patch(f"{_MODULE}._bucket_entity", return_value=_bucket({})):
            config = model_builders.ingestor_config_for_bucket("contracts")

        assert config.llm_model == "text-generation/default-llm"
        assert config.embedding_model == "embedding/default"
        assert config.with_figure_descriptions is False
        assert config.name.en == "Contracts"

    def test_stored_values_override_the_deployment_defaults(self, deployment_defaults):
        stored = {"llm_model": "text-generation/picked", "with_summary_nodes": False}
        with patch(f"{_MODULE}._bucket_entity", return_value=_bucket(stored)):
            config = model_builders.ingestor_config_for_bucket("contracts")

        assert config.llm_model == "text-generation/picked"
        assert config.with_summary_nodes is False
        assert config.with_table_refinement is True

    def test_a_stored_null_means_the_deployment_default_not_nothing(self, deployment_defaults):
        """A cleared picker submits ``null``; that must not blank the model."""
        with patch(f"{_MODULE}._bucket_entity", return_value=_bucket({"llm_model": None})):
            assert model_builders.llm_model_name_for_bucket("contracts") == "text-generation/default-llm"

    def test_a_missing_row_falls_back_to_the_deployment_defaults(self, deployment_defaults):
        with patch(f"{_MODULE}._bucket_entity", return_value=None):
            config = model_builders.ingestor_config_for_bucket("orphan")

        assert config.embedding_model == "embedding/default"
        assert config.name.en == "orphan"

    def test_a_custom_pipeline_reads_its_own_knobs_typed(self, deployment_defaults):
        class CrawlConfig(DocumentIngestionConfig):
            crawl_depth: Annotated[int | None, Field(description="How deep to crawl")] = None

        with patch(f"{_MODULE}._bucket_entity", return_value=_bucket({"crawl_depth": 3})):
            config = model_builders.ingestor_config_for_bucket("sites", CrawlConfig)

        assert config.crawl_depth == 3


class TestVisionModel:
    def test_the_vision_model_falls_back_to_the_text_model(self, deployment_defaults):
        with patch(f"{_MODULE}._bucket_entity", return_value=_bucket({"llm_model": "text-generation/picked"})):
            assert model_builders.vision_model_name_for_bucket("contracts") == "text-generation/picked"

    def test_a_chosen_vision_model_wins_over_the_text_model(self, deployment_defaults):
        stored = {"llm_model": "text-generation/picked", "vision_model": "text-generation/vision"}
        with patch(f"{_MODULE}._bucket_entity", return_value=_bucket(stored)):
            assert model_builders.vision_model_name_for_bucket("contracts") == "text-generation/vision"


class TestEmbeddingDimension:
    def test_a_model_without_declared_width_is_refused_loudly(self, deployment_defaults):
        """Milvus would silently pad or truncate; the pipeline must fail instead."""
        with (
            patch(f"{_MODULE}._bucket_entity", return_value=_bucket({})),
            patch(
                "swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config.EmbeddingModelConfig.get_model_info",
                return_value={"model_info": {}},
            ),
            pytest.raises(ValueError, match="output_vector_size"),
        ):
            model_builders.embedding_dimension_for_bucket("contracts")
