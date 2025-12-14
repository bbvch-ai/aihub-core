from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.agents.NamespaceSelectionAgent.configs.BucketReference import BucketReference
from aihub_agent.agents.RagAgent.configs.RetrievalAgentReference import RetrievalAgentReference


class NamespaceSelectionAgentConfig(AgentConfig):
    """
    Configuration for a NamespaceSelectionAgent.

    The agent asks the user which namespace to use for each configured bucket,
    stores the selection in ThreadContext, and delegates all subsequent messages
    to the configured RAG agent with the selected namespace overrides.
    """

    buckets: Annotated[
        list[BucketReference],
        Field(
            description="List of buckets to select namespaces from (one namespace per bucket).",
            min_length=1,
        ),
    ]

    rag_agent: Annotated[
        RetrievalAgentReference,
        Field(description="The RAG agent to delegate to after namespace selection is complete."),
    ]

    knowledge_retrieval_agent_id: Annotated[
        str,
        Field(
            description="The ID of the KnowledgeRetrievalAgent in the RAG agent's config. "
            "Used to set namespace overrides when delegating."
        ),
    ]

    llm: Annotated[
        LLMConfig,
        Field(description="The LLM configuration for generating questions and parsing responses."),
    ]

    selection_prompt: Annotated[
        LocaleString | None,
        Field(
            default=None,
            description="Custom prompt for asking namespace selection. If not provided, uses default.",
        ),
    ]

    max_selection_attempts: Annotated[
        int,
        Field(
            default=5,
            description="Maximum number of HITL chat rounds for clarification before giving up.",
            ge=1,
            le=10,
        ),
    ]
