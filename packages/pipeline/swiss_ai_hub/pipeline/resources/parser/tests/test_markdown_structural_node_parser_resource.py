"""Tests for wiring the embedding model's input limit into the node parser."""

from unittest.mock import patch

from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

from swiss_ai_hub.pipeline.resources.parser.markdown_structural_node_parser_resource import (
    MarkdownStructuralNodeParserResource,
)


def build_resource() -> MarkdownStructuralNodeParserResource:
    """
    Constructing the resource is the assertion.

    Dagster validates ResourceDependency fields at construction, and `ResourceDependency[T] | None` fails that
    validation — a shape that unit tests missed entirely because they never build the resource, so it would
    only have surfaced when the Dagster code location loaded.
    """
    return MarkdownStructuralNodeParserResource(
        llm_config=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        embedding_config=EmbeddingModelConfig(model_name="embedding/bge-m3"),
    )


class TestMarkdownStructuralNodeParserResource:
    def test_resource_can_be_constructed_with_both_dependencies(self) -> None:
        assert build_resource() is not None

    def test_max_embedding_tokens_comes_from_the_embedding_model(self) -> None:
        resource = build_resource()

        with patch.object(
            EmbeddingModelConfig, "get_model_info", return_value={"model_info": {"max_input_tokens": 4096}}
        ):
            assert resource._resolve_max_embedding_tokens(resource.embedding_config) == 4096

    def test_null_max_input_tokens_falls_back_to_the_default(self) -> None:
        """LiteLLM reports null for any model it holds no metadata for."""
        resource = build_resource()

        with patch.object(
            EmbeddingModelConfig, "get_model_info", return_value={"model_info": {"max_input_tokens": None}}
        ):
            assert resource._resolve_max_embedding_tokens(resource.embedding_config) == 8192

    def test_parser_receives_the_resolved_ceiling(self) -> None:
        resource = build_resource()

        with patch.object(
            EmbeddingModelConfig, "get_model_info", return_value={"model_info": {"max_input_tokens": 4096}}
        ):
            parser = resource.get_node_parser_for_ref_doc(ref_doc=_ref_doc(), document_store_name="store")

        assert parser.max_embedding_tokens == 4096


def _ref_doc():
    from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument

    return RefDocDocument(text="content", extra_info={})
