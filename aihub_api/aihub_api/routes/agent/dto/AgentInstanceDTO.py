from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.nats.events.discovery.agent.AgentInstanceDiscoveryResponseEvent import (
    AgentInstanceDiscoveryResponseEvent,
)
from aihub_lib.persistence.agents.AgentEntity import AgentEntity
from pydantic import Field

from aihub_api.routes.agent.dto.AgentClassDTO import AgentClassDTO


class AgentInstanceDTO(AgentClassDTO):
    """
    Encapsulates the data transfer object (DTO) for an agent class.
    Contains information about the agent class, including its name and configuration specifications.
    """

    agent_id: Annotated[str, Field(description="Unique identifier for the agent instance (e.g., 'agent_123').")]
    agent_config: Annotated[
        AgentConfig,
        Field(description="Configuration details of the agent, including name, description, and prompts."),
    ]

    @classmethod
    def from_class_and_config(cls, class_dto: AgentClassDTO, agent_config: AgentConfig) -> "AgentInstanceDTO":
        """Creates an AgentDTO from an AgentClassDTO and an AgentConfig."""
        return cls(
            agent_class=class_dto.agent_class,
            agent_id=agent_config.agent_id,
            agent_config=agent_config,
            is_conversational=class_dto.is_conversational,
            start_events=class_dto.start_events,
            stop_events=class_dto.stop_events,
            hitl_request_events=class_dto.hitl_request_events,
            hitl_response_events=class_dto.hitl_response_events,
            network_graph=class_dto.network_graph,
            is_online=class_dto.is_online,
            agent_config_specs=class_dto.agent_config_specs,
            default_agent_config=class_dto.default_agent_config,
        )

    def to_discovery_response_event(self) -> AgentInstanceDiscoveryResponseEvent:
        return AgentInstanceDiscoveryResponseEvent(
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            agent_config=self.agent_config,
            default_agent_config=self.default_agent_config,
            agent_config_specs=self.agent_config_specs,
            start_events=self.start_events,
            stop_events=self.stop_events,
            hitl_request_events=self.hitl_request_events,
            hitl_response_events=self.hitl_response_events,
            network_graph=self.network_graph,
            is_conversational=self.is_conversational,
        )

    def create_or_update_agent_entity(self) -> AgentEntity:
        return AgentEntity.create_or_update(
            agent_id=self.agent_id,
            agent_class=self.agent_class,
            default_agent_config=self.default_agent_config,
            agent_config_specs=self.agent_config_specs,
            is_conversational=self.is_conversational,
            start_events=self.start_events,
            stop_events=self.stop_events,
            hitl_request_events=self.hitl_request_events,
            hitl_response_events=self.hitl_response_events,
            network_graph=self.network_graph,
        )
