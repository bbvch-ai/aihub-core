from typing import Annotated

from pydantic import BaseModel, Field


class RAGDelegationConfig(BaseModel):
    """Configuration for delegating queries to a RAG agent."""

    rag_agent_class: Annotated[str, Field(description="The class name of the target RAG agent.")]
    rag_agent_id: Annotated[str, Field(description="The instance ID of the target RAG agent.")]
