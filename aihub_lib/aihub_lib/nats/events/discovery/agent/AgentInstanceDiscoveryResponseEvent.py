from typing import Annotated

from pydantic import Field

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.nats.events.discovery.agent.AgentClassDiscoveryResponseEvent import (
    AgentClassDiscoveryResponseEvent,
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
    def from_agent_instance(cls, agent_instance) -> "AgentInstanceDiscoveryResponseEvent":
        """
        Converts an AgentDTO to an AgentInstanceDiscoveryResponseEvent.
        This is useful for creating a discovery response from a DTO representation of an agent.
        """
        return cls(
            agent_class=agent_instance.agent_class,
            agent_id=agent_instance.agent_id,
            agent_config=agent_instance.agent_config,
            default_agent_config=agent_instance.default_agent_config,
            agent_config_specs=agent_instance.agent_config_specs,
            start_events=agent_instance.start_events,
            stop_events=agent_instance.stop_events,
            network_graph=agent_instance.network_graph,
            is_conversational=agent_instance.is_conversational,
        )
