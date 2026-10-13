"""Chatting with an attached file inlines the document into the user message, and that message is the query the
attached-file ranking and knowledge retrieval embed. bge-m3 rejected it with a 400 (20710 tokens against an
8192 window); the clamp keeps the tail, where the question lives, within the model's budget."""

from unittest.mock import patch

from llama_index.core.utils import get_tokenizer

from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_query_clamp import (
    QUERY_BUDGET_SAFETY_FACTOR,
    EmbeddingQueryClamp,
)

MODEL_CONFIG = "swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_query_clamp.EmbeddingModelConfig"


def _resolving_window(config_cls, window: int | None) -> None:
    config_cls.return_value.get_model_info.return_value = {"model_info": {"max_input_tokens": window}}


def test_document_sized_query_is_clamped_to_the_model_window_keeping_the_question():
    question = "What does the attached contract say about termination?"
    query = ("Contract clause text. " * 6000) + question

    with patch(MODEL_CONFIG) as config_cls:
        _resolving_window(config_cls, 8192)
        clamped = EmbeddingQueryClamp.clamp(query, model_name="embedding/bge-m3")

    assert len(get_tokenizer()(clamped)) <= int(8192 * QUERY_BUDGET_SAFETY_FACTOR)
    assert clamped.endswith(question)


def test_short_query_passes_through_without_resolving_the_window():
    query = "What is the retention period?"

    with patch(MODEL_CONFIG) as config_cls:
        assert EmbeddingQueryClamp.clamp(query, model_name="embedding/bge-m3") is query
        config_cls.assert_not_called()


def test_token_limit_resolves_the_model_window():
    with patch(MODEL_CONFIG) as config_cls:
        _resolving_window(config_cls, 100)
        assert EmbeddingQueryClamp.token_limit("embedding/bge-m3") == int(100 * QUERY_BUDGET_SAFETY_FACTOR)


def test_token_limit_falls_back_to_the_default_window_when_the_model_reports_none():
    with patch(MODEL_CONFIG) as config_cls:
        _resolving_window(config_cls, None)
        assert EmbeddingQueryClamp.token_limit("embedding/bge-m3") == int(8192 * QUERY_BUDGET_SAFETY_FACTOR)


def test_explicit_window_never_resolves_model_info():
    with patch(MODEL_CONFIG) as config_cls:
        assert EmbeddingQueryClamp.token_limit("embedding/bge-m3", max_input_tokens=64) == int(
            64 * QUERY_BUDGET_SAFETY_FACTOR
        )
        config_cls.assert_not_called()
