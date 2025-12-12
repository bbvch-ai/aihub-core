from typing import Annotated

from pydantic import BaseModel, Field


class InsightSourceConfig(BaseModel):
    """
    Configuration for reading insights from a specific namespace.

    Used to specify which insight sources to query when retrieving
    expert-provided insights from MongoDB.
    """

    namespace: Annotated[str, Field(description="The namespace to filter insights by.")]
    agent_class: Annotated[str, Field(description="The agent class to filter insights by.")]
    agent_id: Annotated[str, Field(description="The agent ID to filter insights by.")]
