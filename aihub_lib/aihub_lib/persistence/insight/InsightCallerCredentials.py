from typing import Annotated

from pydantic import BaseModel, Field


class InsightCallerCredentials(BaseModel):
    """Credentials identifying the agent that owns/created an insight.

    Used to pass caller identity through agent chains for insight creation
    and retrieval filtering. Contains the agent_class and agent_id that will
    be used when creating insights.

    This is separate from InsightCreator (MongoEngine EmbeddedDocument) which
    also includes user_id and user_name for persistence.
    """

    agent_class: Annotated[str, Field(description="The agent class that owns the insight")]
    agent_id: Annotated[str, Field(description="The agent ID that owns the insight")]
