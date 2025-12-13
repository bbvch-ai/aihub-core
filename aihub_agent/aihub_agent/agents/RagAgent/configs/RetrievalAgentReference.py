from typing import Annotated

from pydantic import BaseModel, Field


class RetrievalAgentReference(BaseModel):
    """
    Reference to a retrieval agent, containing both agent class and ID.

    Used by RAGAgent and ExpertRAGAgent to specify which retrieval agents to invoke
    during the retrieval step. Both fields are required for AgentInTheLoop invocation.
    """

    agent_class: Annotated[
        str,
        Field(description="The agent class (e.g., 'KnowledgeRetrievalAgent', 'InsightRetrievalAgent')."),
    ]
    agent_id: Annotated[
        str,
        Field(description="The unique agent ID for this retrieval agent instance."),
    ]
