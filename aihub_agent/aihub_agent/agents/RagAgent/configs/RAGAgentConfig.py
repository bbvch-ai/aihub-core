from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.agents.RagAgent.configs.AgentReference import AgentReference
from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig


class RAGAgentConfig(AgentConfig):
    """
    Configuration for a simple RAGAgent without expert escalation.

    Supports:
    - Multi-agent retrieval (0-n agents by ID) - any retrieval agent type
    - Multi-hop retrieval for context sufficiency
    - Shared reranking applied after combining all results

    Note: For expert escalation support, use ExpertRAGAgentConfig.
    """

    llm: Annotated[
        LLMConfig,
        Field(description="The LLM configuration for the agent."),
    ]

    # Unified retrieval agents (0-n) - any retrieval agent type
    retrieval_agents: Annotated[
        list[AgentReference],
        Field(description="List of retrieval agents to invoke (any type: knowledge, insight, sql, etc.)."),
    ] = []

    # Shared reranking (applied after combining all results)
    reranking_config: Annotated[
        RerankingConfig,
        Field(description="Configuration for reranking combined results to improve relevance."),
    ] = RerankingConfig()

    number_of_input_tokens: Annotated[
        int, Field(description="Maximum tokens allowed in input to manage context size or cost.")
    ]
    condense_question_prompt: Annotated[
        LocaleString | None,
        Field(description="Prompt template for transforming a user query into a standalone question."),
    ] = None
    few_shot_guard_examples: Annotated[
        list[FewShotGuardExample],
        Field(description="Examples for the few-shot guard to define which user requests are accepted."),
    ] = []
    check_context_sufficiency: Annotated[
        bool | None,
        Field(
            description="Whether or not to check if the retrieved context is sufficient for generating a response.",
        ),
    ] = False
    max_hops: Annotated[
        int,
        Field(
            description="Maximum number of retrieval hops to perform if context is insufficient.",
            ge=1,
        ),
    ] = 1
    system_prompt: Annotated[
        LocaleString | None,
        Field(description="System prompt to guide the agent's behavior and responses."),
    ] = None
