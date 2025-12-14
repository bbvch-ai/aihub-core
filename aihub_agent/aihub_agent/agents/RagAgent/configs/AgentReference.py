from typing import Annotated

from pydantic import BaseModel, Field


class AgentReference(BaseModel):
    """
    Reference to an agent, containing both agent class and ID.
    """

    agent_class: Annotated[
        str,
        Field(description="The agent class (e.g., 'KnowledgeRetrievalAgent', 'InsightRetrievalAgent')."),
    ]
    agent_id: Annotated[
        str,
        Field(description="The unique agent ID for this retrieval agent instance."),
    ]
