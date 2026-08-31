from dagster import ConfigurableResource, ResourceDependency
from llama_index.core.llms import LLM
from swiss_ai_hub.core.generative_ai.document.parsers.recursive_summary_parser import (
    DEFAULT_SUMMARIZATION_MAX_INPUT_TOKENS,
    RecursiveNodeSummarizer,
)
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

MAX_INPUT_TOKENS_CEILING = DEFAULT_SUMMARIZATION_MAX_INPUT_TOKENS
"""
Hard cap applied to a LiteLLM-declared window, regardless of what LiteLLM echoes. Shares a value with
`RecursiveNodeSummarizer`'s own fallback default today, but the two are separate decisions -- this one is a
deployment-level safety cap, that one is "what to budget when nobody says otherwise" -- and may diverge as
models or providers change.
"""


class RecursiveSummaryParserResource(ConfigurableResource):
    """
    This resource provides a recursive summary parser for nodes.
    It is used to summarize nodes recursively using a language model (LLM).
    """

    llm_config: ResourceDependency[LLMConfig]

    def get_summary_parser(self, llm: LLM) -> RecursiveNodeSummarizer:
        return RecursiveNodeSummarizer(
            llm=llm,
            max_input_tokens=self._resolve_max_input_tokens(),
            token_counter=self.llm_config.token_counter,
        )

    def _resolve_max_input_tokens(self) -> int:
        """
        Cap the declared window rather than trust it: LiteLLM echoes whatever we hand-configured for a
        model, and the provider's OpenAI-compatible endpoint carries no context-length field for LiteLLM to
        cross-check it against.
        """
        declared = self.llm_config.get_model_info()["model_info"].get("max_input_tokens")
        return min(declared or MAX_INPUT_TOKENS_CEILING, MAX_INPUT_TOKENS_CEILING)
