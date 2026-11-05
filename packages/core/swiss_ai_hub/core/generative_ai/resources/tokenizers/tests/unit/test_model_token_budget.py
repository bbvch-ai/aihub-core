"""Budget sites learn from the model's LiteLLM entry whether they can count exactly. Every chat model and any
embedder added without a vendored tokenizer keep the tiktoken count and safety factors they had; only embedders and
rerankers announce that they do."""

import logging
from collections.abc import Iterator

import pytest

from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_token_budget import (
    DEFAULT_MAX_INPUT_TOKENS,
    ModelTokenBudget,
)
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_tokenizer import FALLBACK_TOKENIZER_ID

MODULE = "swiss_ai_hub.core.generative_ai.resources.tokenizers.model_token_budget"
DECLARED = {
    "mode": "embedding",
    "max_input_tokens": 8192,
    "aihub_tokenizer": "bge-m3",
    "aihub_input_overhead_tokens": 2,
}


@pytest.fixture
def no_warnings_yet() -> Iterator[None]:
    warned = set(ModelTokenBudget._warned_models)
    ModelTokenBudget._warned_models.clear()
    yield
    ModelTokenBudget._warned_models.clear()
    ModelTokenBudget._warned_models.update(warned)


def test_declared_model_counts_exactly_with_its_own_tokenizer() -> None:
    budget = ModelTokenBudget.for_model("embedding/bge-m3", DECLARED)

    assert budget.exact
    assert budget.tokenizer.tokenizer_id == "bge-m3"
    assert budget.usable_input_tokens == 8190
    assert budget.count_with_overhead("Hallo") == budget.tokenizer.count("Hallo") + 2


def test_explicit_window_wins() -> None:
    assert ModelTokenBudget.for_model("embedding/bge-m3", DECLARED, max_input_tokens=1024).max_input_tokens == 1024


def test_undeclared_embedding_model_falls_back_and_warns_once(caplog, no_warnings_yet) -> None:
    with caplog.at_level(logging.WARNING, logger=MODULE):
        first = ModelTokenBudget.for_model("embedding/other", {"mode": "embedding", "max_input_tokens": 512})
        ModelTokenBudget.for_model("embedding/other", {"mode": "embedding", "max_input_tokens": 512})

    assert not first.exact
    assert first.tokenizer_id == FALLBACK_TOKENIZER_ID
    assert first.max_input_tokens == 512
    assert first.input_overhead_tokens == 0
    assert [record.args[0] for record in caplog.records] == ["embedding/other"]


def test_undeclared_reranker_warns(caplog, no_warnings_yet) -> None:
    with caplog.at_level(logging.WARNING, logger=MODULE):
        ModelTokenBudget.for_model("reranker/other", {"mode": "rerank"})

    assert len(caplog.records) == 1


def test_undeclared_chat_model_stays_quiet(caplog, no_warnings_yet) -> None:
    with caplog.at_level(logging.WARNING, logger=MODULE):
        budget = ModelTokenBudget.for_model("text-generation/gemma", {"mode": "chat", "max_input_tokens": 91824})

    assert not budget.exact
    assert not caplog.records


def test_missing_window_falls_back_to_the_default() -> None:
    assert ModelTokenBudget.for_model("embedding/other", {}).max_input_tokens == DEFAULT_MAX_INPUT_TOKENS


def test_tokenizer_that_is_not_vendored_raises_naming_model_and_id() -> None:
    with pytest.raises(ValueError, match="embedding/new.*e5-large"):
        ModelTokenBudget.for_model("embedding/new", {**DECLARED, "aihub_tokenizer": "e5-large"})


def test_tokenizer_without_overhead_raises() -> None:
    declared_without_overhead = {key: value for key, value in DECLARED.items() if key != "aihub_input_overhead_tokens"}

    with pytest.raises(ValueError, match="aihub_input_overhead_tokens"):
        ModelTokenBudget.for_model("embedding/bge-m3", declared_without_overhead)


def test_token_budget_reads_the_model_info_the_config_already_resolves(monkeypatch) -> None:
    monkeypatch.setattr(EmbeddingModelConfig, "get_model_info", lambda self: {"model_info": DECLARED})

    assert EmbeddingModelConfig(model_name="embedding/bge-m3").token_budget().exact


def test_chat_token_counter_stays_tiktoken() -> None:
    """Phase 1 leaves chat budgets and cost tracking on tiktoken; the shared hook is not model-aware."""
    config = LLMConfig(model_name="text-generation/gemma-4-31B-it")

    assert len(config.token_counter("hello world")) == 2
