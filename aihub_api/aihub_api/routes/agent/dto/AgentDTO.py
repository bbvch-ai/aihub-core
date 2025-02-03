from typing import List

from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig
from aihub_lib.nats.events.discovery.AgentDiscoveryResponseEvent import StartEventSpecs
from pydantic import BaseModel, Field


class AgentDTO(BaseModel):
    """
    A data transfer object for representing agent information in responses.

    ### Why AgentDTO?
    This DTO standardizes how agent data is returned from the service layer to the controller,
    and subsequently to the API response. It helps maintain a clean separation between the internal
    event models and the publicly exposed fields in HTTP responses.

    By using `AgentDTO`, the API can evolve independently from the internal event representations.
    """

    agent_class: str = Field(..., description="The agent's class identifier (e.g., 'my_agent_class').")
    agent_id: str = Field(..., description="Unique identifier for the agent instance (e.g., 'agent_123').")
    agent_config: AgentConfig = Field(
        ..., description="Configuration details of the agent, including name, description, and prompts."
    )
    start_events: List[StartEventSpecs] = Field(
        ..., description="A list of `StartEventSpecs` representing events that can start this agent's workflow."
    )
