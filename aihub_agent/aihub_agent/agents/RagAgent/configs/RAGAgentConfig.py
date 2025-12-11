from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field


class RAGAgentConfig(AgentConfig):
    """
    Configuration for a simple RAGAgent without expert escalation.

    Supports:
    - Multi-hop retrieval for context sufficiency
    - Shared retrieval via RetrievalAgent (configured separately)

    The retrieval settings (retrievers, reranking, context_prompt) are configured
    in the referenced RetrievalAgent's config, not here.

    Note: For expert escalation support, use ExpertRAGAgentConfig.
    """

    llm: Annotated[
        LLMConfig,
        Field(description="The LLM configuration for the agent."),
    ]

    # RetrievalAgent reference for AgentInTheLoop invocation
    retrieval_agent_class: Annotated[
        str,
        Field(description="Agent class name of the RetrievalAgent to invoke."),
    ] = "RetrievalAgent"
    retrieval_agent_id: Annotated[
        str,
        Field(description="Agent ID of the RetrievalAgent to invoke."),
    ] = "default"

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
