from dagster import ConfigurableResource
from llama_index.core.llms import LLM
from swiss_ai_hub.core.generative_ai.document.parsers.RecursiveSummaryParser import RecursiveNodeSummarizer


class RecursiveSummaryParserResource(ConfigurableResource):
    """
    This resource provides a recursive summary parser for nodes.
    It is used to summarize nodes recursively using a language model (LLM).
    """

    def get_summary_parser(self, llm: LLM) -> RecursiveNodeSummarizer:
        return RecursiveNodeSummarizer(llm=llm)
