from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.agents.step_configs import KnowledgeRetrievalStepConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig


class KnowledgeRetrievalAgentConfig(AgentConfig):
    """
    Configuration for the KnowledgeRetrievalAgent.

    Contains all settings needed for knowledge (vector store) retrieval:
    - Retrieval step config with embed model, vector store, and default namespaces
    - Optional reranking
    - Context prompt template
    """

    retrieval: Annotated[
        KnowledgeRetrievalStepConfig,
        Field(description="Knowledge retrieval step configuration with vector store and embedding model."),
    ]

    reranking_config: Annotated[
        RerankingConfig,
        Field(description="Configuration for reranking retrieved documents to improve relevance."),
    ] = RerankingConfig()

    context_prompt: Annotated[
        LocaleString | None,
        Field(description="Prompt template for combining retrieved nodes into context."),
    ] = None
