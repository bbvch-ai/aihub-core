import math
from unittest.mock import MagicMock, patch

import pytest
from llama_index.core.callbacks import TokenCountingHandler
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI

from lib_core.handlers.CostTracker import CostTracker
from lib_core.handlers.LLMHandler import LLMHandler
from lib_core.records.agent.Costs import Costs


@pytest.fixture
def llm_handler():
    with patch("llama_index.core.instrumentation.get_dispatcher") as mock_dispatcher:
        dispatcher_instance = MagicMock()
        dispatcher_instance.event_handlers = [MagicMock(class_name="ObservationContext")]
        mock_dispatcher.return_value = dispatcher_instance
        return LLMHandler(organization="test_org")


@pytest.fixture
def token_counter():
    token_counter = MagicMock(spec=TokenCountingHandler)
    token_counter.prompt_llm_token_count = 100
    token_counter.completion_llm_token_count = 200
    token_counter.total_embedding_token_count = 50
    return token_counter


@pytest.fixture
def cost_tracker(token_counter):
    return CostTracker(
        token_counter=token_counter,
        prompt_tokens_costs_per_thousand=1.0,
        completion_tokens_costs_per_thousand=2.0,
        embedding_tokens_costs_per_thousand=0.5,
    )


@pytest.fixture
def initial_costs(llm_handler):
    expected_costs = Costs(
        prompt_token_count=0,
        completion_token_count=0,
        embedding_token_count=0,
        prompt_tokens_costs=0.0,
        completion_tokens_costs=0.0,
        embedding_tokens_costs=0.0,
    )
    return expected_costs


def test_get_total_costs_initial(llm_handler, initial_costs):
    assert llm_handler.get_total_costs() == initial_costs, "Initial costs should be all zeros"


def test_cost_tracking(cost_tracker, llm_handler):
    llm_handler._cost_trackers.append(cost_tracker)
    costs = llm_handler.get_total_costs()
    expected_costs = Costs(
        prompt_token_count=100,
        completion_token_count=200,
        embedding_token_count=50,
        prompt_tokens_costs=0.1,
        completion_tokens_costs=0.4,
        embedding_tokens_costs=0.025,
    )
    assert costs == expected_costs, "Cost tracking did not calculate costs correctly"


def test_get_total_costs(llm_handler):
    some_cost_tracker = MagicMock()
    some_cost_tracker.get_total_costs.return_value = Costs(
        prompt_token_count=1000,
        completion_token_count=2000,
        embedding_token_count=3000,
        prompt_tokens_costs=1.0,
        completion_tokens_costs=4.0,
        embedding_tokens_costs=1.5,
    )
    llm_handler._cost_trackers = [some_cost_tracker, some_cost_tracker]
    total_costs = llm_handler.get_total_costs()
    assert total_costs.prompt_token_count == 2000
    assert total_costs.completion_token_count == 4000
    assert total_costs.embedding_token_count == 6000
    assert math.isclose(total_costs.prompt_tokens_costs, 2.0, rel_tol=1e-09, abs_tol=1e-09)
    assert math.isclose(total_costs.completion_tokens_costs, 8.0, rel_tol=1e-09, abs_tol=1e-09)
    assert math.isclose(total_costs.embedding_tokens_costs, 3.0, rel_tol=1e-09, abs_tol=1e-09)


@pytest.mark.parametrize(
    "model_name, expected_class, model_param",
    [
        ("gpt-4o", AzureOpenAI, None),
        ("text-embedding-ada-002", AzureOpenAIEmbedding, None),
        ("invalid-model", None, None),
    ],
)
@patch("aihub.entities.LLM.factory.LLMEntityFactory.LLMEntityFactory.by_name")
def test_model_by_name(mock_by_name, model_name, expected_class, model_param):
    mock_model_entity = MagicMock()
    mock_model = MagicMock(spec=expected_class) if expected_class else None
    mock_cost_tracker = MagicMock()

    if expected_class:
        mock_model_entity.to_llama_index.return_value = (mock_model, mock_cost_tracker)
    else:
        mock_by_name.side_effect = ValueError("Invalid model")

    mock_by_name.return_value = mock_model_entity

    handler = LLMHandler(organization="test-org")

    if expected_class:
        result = handler.model_by_name(model_name, model_param)
        assert isinstance(result, expected_class), f"Expected {expected_class}, but got {type(result)}"
        mock_model_entity.to_llama_index.assert_called_once_with(model_param)
        assert mock_cost_tracker in handler._cost_trackers, "Cost tracker should be added to the list"
    else:
        with pytest.raises(ValueError, match="Invalid model"):
            handler.model_by_name(model_name, model_param)


def test_cost_calculation_accuracy(llm_handler, cost_tracker):
    llm_handler._cost_trackers.append(cost_tracker)
    llm_handler._cost_trackers.append(cost_tracker)
    costs = llm_handler.get_total_costs()
    expected_prompt_cost = (100 * 1.0 / 1000) * 2
    expected_completion_cost = (200 * 2.0 / 1000) * 2
    expected_embedding_cost = (50 * 0.5 / 1000) * 2
    assert costs.prompt_tokens_costs == expected_prompt_cost, "Incorrect prompt tokens costs"
    assert costs.completion_tokens_costs == expected_completion_cost, "Incorrect completion tokens costs"
    assert costs.embedding_tokens_costs == expected_embedding_cost, "Incorrect embedding tokens costs"
