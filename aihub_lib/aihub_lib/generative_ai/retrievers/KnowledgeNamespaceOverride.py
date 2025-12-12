from typing import Annotated

from pydantic import BaseModel, Field


class KnowledgeNamespaceOverride(BaseModel):
    """
    Override configuration for a specific knowledge retrieval agent.

    Used in events to override which namespaces to search at runtime.
    The agent_id references a KnowledgeRetrievalAgent instance.
    """

    agent_id: Annotated[str, Field(description="The retrieval agent ID to override.")]
    namespaces: Annotated[list[str], Field(description="Override namespaces for this agent.", min_length=1)]
