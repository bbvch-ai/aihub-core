from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import BaseModel, Field


class AllowedBucketConfig(BaseModel):
    """Configuration for an allowed knowledge bucket."""

    bucket_name: Annotated[str, Field(description="The name of the bucket/collection in Milvus")]
    retrieve_k: Annotated[int, Field(description="Number of documents to retrieve per query", ge=1)] = 10


class NamespaceSelectionAgentConfig(AgentConfig):
    """
    Configuration for NamespaceSelectionAgent.

    The NamespaceSelectionAgent orchestrates knowledge source selection before
    delegating to RAGAgent. It uses LLM-based analysis to select relevant
    namespaces and supports clarification loops when selection is uncertain.
    """

    selection_llm: Annotated[
        LLMConfig,
        Field(description="LLM configuration for namespace selection and clarification"),
    ]

    embed_model: Annotated[
        EmbeddingModelConfig,
        Field(description="Embedding model for topic change detection"),
    ]

    allowed_buckets: Annotated[
        list[AllowedBucketConfig],
        Field(description="List of buckets this agent is allowed to select namespaces from", min_length=1),
    ]

    rag_agent_class: Annotated[
        str,
        Field(description="The agent class to delegate RAG processing to"),
    ] = "RAGAgent"

    rag_agent_id: Annotated[
        str,
        Field(description="The agent ID to delegate RAG processing to"),
    ]

    confidence_threshold: Annotated[
        float,
        Field(
            description="Minimum confidence score (0.0-1.0) required to proceed without clarification",
            ge=0.0,
            le=1.0,
        ),
    ] = 0.7

    auto_switch_threshold: Annotated[
        float,
        Field(
            description="Similarity threshold (0.0-1.0) below which topic is considered changed",
            ge=0.0,
            le=1.0,
        ),
    ] = 0.5

    remember_selection: Annotated[
        bool,
        Field(description="Whether to persist namespace selection in ThreadContext"),
    ] = True

    max_clarification_rounds: Annotated[
        int,
        Field(description="Maximum number of HITL clarification loops before forcing selection", ge=1),
    ] = 3

    selection_system_prompt: Annotated[
        LocaleString | None,
        Field(description="System prompt for namespace selection LLM calls"),
    ] = None

    clarification_prompt: Annotated[
        LocaleString | None,
        Field(description="Prompt template for generating clarification questions"),
    ] = None
