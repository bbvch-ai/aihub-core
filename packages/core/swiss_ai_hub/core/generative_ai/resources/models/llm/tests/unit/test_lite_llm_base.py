from unittest.mock import patch

from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig


def _deny_network(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("token_counter must not perform network I/O")


def test_token_counter_tokenizes_locally_without_network():
    config = LLMConfig(model_name="text-generation/gemma-4-31B-it")

    with patch(
        "swiss_ai_hub.core.generative_ai.resources.models.llm.lite_llm_base.LiteLLMProxySettings",
        side_effect=_deny_network,
    ):
        tokens = config.token_counter("hello world")

    assert tokens == config.token_counter("hello world")
    assert len(tokens) > 0


def test_token_counter_is_stable_across_property_accesses():
    config = LLMConfig(model_name="text-generation/gemma-4-31B-it")

    assert config.token_counter("The quick brown fox.") == config.token_counter("The quick brown fox.")
