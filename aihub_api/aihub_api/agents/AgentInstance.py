from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from pydantic import Field

from aihub_api.agents.AgentClass import AgentClass


class AgentInstance(AgentClass):
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
    def from_class_and_config(cls, class_dto: AgentClass, agent_config: AgentConfig) -> "AgentInstance":
        """Creates an AgentDTO from an AgentClassDTO and an AgentConfig."""
        return cls(
            agent_class=class_dto.agent_class,
            agent_id=agent_config.agent_id,
            agent_config=agent_config,
            is_conversational=class_dto.is_conversational,
            start_events=class_dto.start_events,
            stop_events=class_dto.stop_events,
            network_graph=class_dto.network_graph,
            is_online=class_dto.is_online,
            agent_config_specs=class_dto.agent_config_specs,
            default_agent_config=class_dto.default_agent_config,
        )
