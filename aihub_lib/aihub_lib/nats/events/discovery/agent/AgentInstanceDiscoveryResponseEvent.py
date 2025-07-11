from typing import Annotated, Any

from pydantic import Field

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.nats.events.discovery.agent.AgentClassDiscoveryResponseEvent import (
    AgentClassDiscoveryResponseEvent,
    EventSpecs,
)


class AgentInstanceDiscoveryResponseEvent(AgentClassDiscoveryResponseEvent):
    """
    A response event sent after an agent discovery request, detailing an agent's class, ID, configuration,
    and the set of start events it can handle.

    ### Why AgentDiscoveryResponseEvent?
    After a discovery request, consumers need to know:
    - Which agent instance is available (identified by `agent_class` and `agent_id`).
    - What configuration that agent operates under (e.g., model parameters, runtime settings).
    - Which start events the agent can process to begin its workflow.
    - Which stop events the agent might respond with.

    By providing this structured information, the discovery response helps orchestrators and clients
    dynamically integrate with newly discovered agents without manual configuration or guesswork.

    """

    agent_id: Annotated[str, Field(description="A unique identifier for the agent instance.")]
    agent_config: Annotated[
        AgentConfig,
        Field(
            description="The agent's configuration object, containing details like the model used, "
            "temperature settings, or other domain-specific parameters.",
        ),
    ]

    @classmethod
    def from_agent_dto(cls, agent_dto) -> "AgentInstanceDiscoveryResponseEvent":
        """
        Converts an AgentDTO to an AgentInstanceDiscoveryResponseEvent.
        This is useful for creating a discovery response from a DTO representation of an agent.
        """
        return cls(
            agent_class=agent_dto.agent_class,
            agent_id=agent_dto.agent_id,
            agent_config=agent_dto.agent_config,
            agent_config_specs=agent_dto.agent_config_specs,
            start_events=agent_dto.start_events,
            stop_events=agent_dto.stop_events,
            network_graph=agent_dto.network_graph,
            is_conversational=agent_dto.is_conversational,
        )
