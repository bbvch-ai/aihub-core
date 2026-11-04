"""Chatting with an attached file inlines the document into the user message, and that message is the query the
attached-file ranking and knowledge retrieval embed. bge-m3 rejected it with a 400 (20710 tokens against an
8192 window); the clamp keeps the tail, where the question lives, within the model's budget."""

from unittest.mock import patch

from llama_index.core.utils import get_tokenizer

from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_query_clamp import (
    QUERY_BUDGET_SAFETY_FACTOR,
    EmbeddingQueryClamp,
)
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_token_budget import ModelTokenBudget
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_tokenizer import ModelTokenizer

QUESTION = "What does the attached contract say about termination?"
DECLARED = {
    "mode": "embedding",
    "max_input_tokens": 8192,
    "aihub_tokenizer": "bge-m3",
    "aihub_input_overhead_tokens": 2,
}
UNDECLARED = {"mode": "embedding", "max_input_tokens": 8192}


def _model_info(model_info: dict):
    return patch.object(EmbeddingModelConfig, "get_model_info", return_value={"model_info": model_info})


def test_undeclared_model_keeps_half_the_window_in_tiktoken():
    query = ("Contract clause text. " * 6000) + QUESTION

    with _model_info(UNDECLARED):
        clamped = EmbeddingQueryClamp.clamp(query, model_name="embedding/bge-m3")

    assert len(get_tokenizer()(clamped)) <= int(8192 * QUERY_BUDGET_SAFETY_FACTOR)
    assert clamped.endswith(QUESTION)


def test_declared_model_fills_its_whole_window_counted_exactly():
    query = ("def handler(event):\n    return {'status': 200}\n\n" * 3000) + QUESTION
    bge_m3 = ModelTokenizer.shared("bge-m3")

    with _model_info(DECLARED):
        clamped = EmbeddingQueryClamp.clamp(query, model_name="embedding/bge-m3")

    assert bge_m3.count(clamped) + 2 <= 8192
    assert bge_m3.count(clamped) + 2 > 8000
    assert clamped.endswith(QUESTION)


def test_explicit_window_wins_over_the_declared_one():
    query = ("Contract clause text. " * 200) + QUESTION

    with _model_info(DECLARED):
        clamped = EmbeddingQueryClamp.clamp(query, model_name="embedding/bge-m3", max_input_tokens=64)

    assert ModelTokenizer.shared("bge-m3").count(clamped) <= 62


def test_short_query_passes_through_without_resolving_the_window():
    query = "What is the retention period?"

    with patch.object(EmbeddingModelConfig, "get_model_info", side_effect=AssertionError("resolved")):
        assert EmbeddingQueryClamp.clamp(query, model_name="embedding/bge-m3") is query


def test_token_limit_of_a_declared_model_is_its_window_less_its_special_tokens():
    budget = ModelTokenBudget.for_model("embedding/bge-m3", DECLARED)

    assert EmbeddingQueryClamp.token_limit(budget) == 8190


def test_token_limit_of_an_undeclared_model_is_half_its_window():
    budget = ModelTokenBudget.for_model("embedding/other", {"max_input_tokens": 100})

    assert EmbeddingQueryClamp.token_limit(budget) == int(100 * QUERY_BUDGET_SAFETY_FACTOR)


def test_token_limit_falls_back_to_the_default_window_when_the_model_reports_none():
    budget = ModelTokenBudget.for_model("embedding/other", {"max_input_tokens": None})

    assert EmbeddingQueryClamp.token_limit(budget) == int(8192 * QUERY_BUDGET_SAFETY_FACTOR)
