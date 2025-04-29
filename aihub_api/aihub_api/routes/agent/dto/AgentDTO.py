from typing import List

from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.discovery.AgentDiscoveryResponseEvent import EventSpecs
from aihub_lib.persistence.agents.AgentEntity import AgentEntity
from pydantic import BaseModel, Field

from aihub_api.routes.agent.dto.AgentConfigDTO import AgentConfigDTO

class MinimalAgentDTO(BaseModel):
    """
    Encapsulates the data transfer object (DTO) for a minimal agent.
    Only contains minimal information about the agent.
    """
    agent_class: str = Field(..., description="The agent's class identifier (e.g., 'my_agent_class').")
    agent_id: str = Field(..., description="Unique identifier for the agent instance (e.g., 'agent_123').")
    agent_config: AgentConfigDTO = Field(
        ..., description="Configuration details of the agent, including name, description, and prompts."
    )
    is_conversational: bool = Field(..., description="Whether the agent can participate in a chat-based conversation")

    @classmethod
    def from_entity(cls, entity: AgentEntity, t: LocaleHandler) -> "MinimalAgentDTO":
        """Converts an AgentEntity to an AgentDTO."""
        agent_config_dto = AgentConfigDTO.from_agent_config(entity.agent_config, t)
        return cls(
            agent_class=entity.agent_class,
            agent_id=entity.agent_id,
            agent_config=agent_config_dto,
            is_conversational=entity.is_conversational,
        )

class AgentDTO(MinimalAgentDTO):
    """
    A data transfer object for representing agent information in responses.

    ### Why AgentDTO?
    This DTO standardizes how agent data is returned from the service layer to the controller,
    and subsequently to the API response. It helps maintain a clean separation between the internal
    event models and the publicly exposed fields in HTTP responses.

    By using `AgentDTO`, the API can evolve independently from the internal event representations.
    """
    start_events: List[EventSpecs] = Field(
        ..., description="A list of `EventSpecs` representing events that can start this agent's workflow."
    )
    stop_events: List[EventSpecs] = Field(
        ..., description="A list of `EventSpecs` representing events that can stop this agent's workflow."
    )
    network_graph: WorkflowGraph = Field(
        ...,
        description="A network graph of the agent, showing how different components are connected and interact.",
    )

    @classmethod
    def from_entity(cls, entity: AgentEntity, t: LocaleHandler) -> "AgentDTO":
        """Converts an AgentEntity to an AgentDTO."""
        agent_config_dto = AgentConfigDTO.from_agent_config(entity.agent_config, t)

        start_events = [
            EventSpecs(event_name=event.event_name, event_schema=event.event_schema) for event in entity.start_events
        ]

        stop_events = [
            EventSpecs(event_name=event.event_name, event_schema=event.event_schema) for event in entity.stop_events
        ]

        network_graph = WorkflowGraph.model_validate(entity.network_graph)

        return cls(
            agent_class=entity.agent_class,
            agent_id=entity.agent_id,
            agent_config=agent_config_dto,
            is_conversational=entity.is_conversational,
            start_events=start_events,
            stop_events=stop_events,
            network_graph=network_graph,
        )
