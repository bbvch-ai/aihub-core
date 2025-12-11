from typing import Annotated

from pydantic import BaseModel, Field


class ExpertEscalationConfig(BaseModel):
    """
    Configuration for expert escalation workflow.

    When configured in ExpertRAGAgentConfig, this enables the agent to escalate
    to human experts when retrieved context is insufficient to answer the user's query.
    """

    expert_asking_agent_class: Annotated[
        str,
        Field(description="The agent class for expert escalation."),
    ]
    expert_asking_agent_id: Annotated[
        str,
        Field(description="The agent ID for expert escalation."),
    ]
