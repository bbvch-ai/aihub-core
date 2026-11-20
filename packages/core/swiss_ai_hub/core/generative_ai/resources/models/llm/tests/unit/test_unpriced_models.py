"""A model LiteLLM has no price for is usable and costs nothing, rather than failing when it is built."""

from unittest.mock import Mock, patch

import pytest

from swiss_ai_hub.core.generative_ai.resources.costs.llm_cost_tracker import LLMCostTracker
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.reranking_model_config import RerankingModelConfig

pytestmark = pytest.mark.unit

_MODULE = "swiss_ai_hub.core.generative_ai.resources.models.llm"

_UNPRICED_CHAT = {
    "model_info": {
        "max_input_tokens": 8192,
        "mode": "chat",
        "supports_function_calling": True,
        "max_output_tokens": 2048,
        "input_cost_per_token": None,
        "output_cost_per_token": None,
    }
}
_UNPRICED_INPUT_ONLY = {"model_info": {"input_cost_per_token": None}}


def _settings() -> Mock:
    return Mock(
        BASE_URL="http://litellm-test/v1",
        API_KEY=Mock(get_secret_value=Mock(return_value="key")),
        CONNECT_TIMEOUT_SECONDS=5.0,
    )


def _cost_tracker_of(config, module: str, model_info: dict) -> LLMCostTracker:
    with (
        patch.object(type(config), "get_model_info", return_value=model_info),
        patch(f"{_MODULE}.{module}.LiteLLMProxySettings", return_value=_settings()),
    ):
        _, cost_tracker = config.to_llama_index()
    return cost_tracker


def test_a_missing_price_counts_as_zero_per_thousand_tokens() -> None:
    assert LLMCostTracker.per_thousand(None) == 0


def test_a_price_per_token_is_turned_into_a_price_per_thousand_tokens() -> None:
    assert LLMCostTracker.per_thousand(0.000002) == pytest.approx(0.002)


@pytest.mark.parametrize(
    ("config", "module", "model_info"),
    [
        (LLMConfig(model_name="text-generation/gpt-oss-120b"), "llm_config", _UNPRICED_CHAT),
        (EmbeddingModelConfig(model_name="embedding/unpriced"), "embedding_model_config", _UNPRICED_INPUT_ONLY),
        (RerankingModelConfig(model_name="reranker/unpriced"), "reranking_model_config", _UNPRICED_INPUT_ONLY),
    ],
    ids=["chat", "embedding", "rerank"],
)
def test_an_unpriced_model_is_built_and_costs_nothing(config, module: str, model_info: dict) -> None:
    cost_tracker = _cost_tracker_of(config, module, model_info)

    costs = cost_tracker.get_total_costs()

    assert costs.prompt_tokens_costs + costs.completion_tokens_costs + costs.embedding_tokens_costs == 0
