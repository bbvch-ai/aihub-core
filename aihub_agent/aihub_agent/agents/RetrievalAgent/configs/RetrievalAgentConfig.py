from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.retrievers import RetrieverConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig


class RetrievalAgentConfig(AgentConfig):
    """
    Configuration for the RetrievalAgent.

    Contains all settings needed for the retrieval pipeline:
    - Multiple retrievers (knowledge base and/or insights)
    - Optional reranking
    - Context prompt template
    """

    retrievers: Annotated[
        list[RetrieverConfig],
        Field(description="List of retriever configurations (knowledge, insight)."),
    ]

    reranking_config: Annotated[
        RerankingConfig,
        Field(description="Configuration for reranking retrieved documents to improve relevance."),
    ] = RerankingConfig()

    context_prompt: Annotated[
        LocaleString | None,
        Field(description="Prompt template for combining retrieved nodes into context."),
    ] = None
