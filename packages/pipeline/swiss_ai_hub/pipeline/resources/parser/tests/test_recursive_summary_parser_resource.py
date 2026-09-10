"""Tests for wiring the LLM's input limit and tokenizer into the recursive summary parser."""

from unittest.mock import PropertyMock, patch

from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

from swiss_ai_hub.pipeline.resources.parser.recursive_summary_parser_resource import (
    MAX_INPUT_TOKENS_CEILING,
    RecursiveSummaryParserResource,
)


def llm_config() -> LLMConfig:
    """The per-run model config the op resolves from the knowledge database and hands to the resource."""
    return LLMConfig(model_name="text-generation/gemma-4-31B-it")


class TestRecursiveSummaryParserResource:
    def test_resource_carries_no_model_of_its_own(self) -> None:
        """One resource serves every database; the model arrives per run."""
        assert RecursiveSummaryParserResource() is not None

    def test_overstated_declared_limit_is_capped_to_the_default(self) -> None:
        """The model in use declares 131072 and is served at 100000 by the provider."""
        with patch.object(LLMConfig, "get_model_info", return_value={"model_info": {"max_input_tokens": 131072}}):
            assert RecursiveSummaryParserResource._resolve_max_input_tokens(llm_config()) == MAX_INPUT_TOKENS_CEILING

    def test_smaller_declared_limit_is_respected(self) -> None:
        with patch.object(LLMConfig, "get_model_info", return_value={"model_info": {"max_input_tokens": 8192}}):
            assert RecursiveSummaryParserResource._resolve_max_input_tokens(llm_config()) == 8192

    def test_null_max_input_tokens_falls_back_to_the_default(self) -> None:
        """LiteLLM reports null for any model it holds no metadata for."""
        with patch.object(LLMConfig, "get_model_info", return_value={"model_info": {"max_input_tokens": None}}):
            assert RecursiveSummaryParserResource._resolve_max_input_tokens(llm_config()) == MAX_INPUT_TOKENS_CEILING

    def test_summary_parser_receives_the_resolved_ceiling_and_token_counter(self) -> None:
        resource = RecursiveSummaryParserResource()
        sentinel_counter = lambda text: [0] * len(text)  # noqa: E731 - identity-checked below, not called

        with (
            patch.object(LLMConfig, "get_model_info", return_value={"model_info": {"max_input_tokens": 8192}}),
            patch.object(LLMConfig, "token_counter", new_callable=PropertyMock, return_value=sentinel_counter),
        ):
            summary_parser = resource.get_summary_parser(llm=object(), llm_config=llm_config())

        assert summary_parser._max_input_tokens == 8192
        assert summary_parser._token_counter is sentinel_counter
