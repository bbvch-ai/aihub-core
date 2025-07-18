import logging
from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.nats.events.discovery.agent.AgentClassDiscoveryResponseEvent import (
    AgentClassDiscoveryResponseEvent,
    AgentConfigSpecs,
)
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs
from pydantic import BaseModel, Field


class AgentClassDTO(BaseModel):
    """
    Encapsulates the data transfer object (DTO) for an agent class.
    Contains information about the agent class, including its name and configuration specifications.
    """

    agent_class: Annotated[str, Field(description="The agent's class identifier (e.g., 'my_agent_class').")]
    agent_config_specs: Annotated[
        AgentConfigSpecs,
        Field(description="Configuration specifications of the agent class, including schema and parameters."),
    ]
    start_events: Annotated[
        list[EventSpecs],
        Field(description="A list of `EventSpecs` representing events that can start this agent's workflow."),
    ]
    stop_events: Annotated[
        list[EventSpecs],
        Field(description="A list of `EventSpecs` representing events that can stop this agent's workflow."),
    ]
    network_graph: Annotated[
        WorkflowGraph,
        Field(
            description="A network graph of the agent class, "
            "showing how different components are connected and interact.",
        ),
    ]
    is_conversational: Annotated[
        bool, Field(description="Whether the agent class can participate in a chat-based conversation")
    ]
    is_online: Annotated[
        bool | None, Field(description="Indicates whether the agent class is online and reachable.")
    ] = None
    default_agent_config: Annotated[
        AgentConfig,
        Field(
            description="The default agent configuration for this agent class. "
            "This is the configuration that will be used if no specific configuration is provided.",
        ),
    ]

    @classmethod
    def from_discovery_event(
        cls,
        event: AgentClassDiscoveryResponseEvent,
    ) -> "AgentClassDTO":
        """Converts an AgentClassDiscoveryResponseEvent to an AgentClassDTO."""
        return cls(
            agent_class=event.agent_class,
            agent_config_specs=event.agent_config_specs,
            is_conversational=event.is_conversational,
            start_events=event.start_events,
            stop_events=event.stop_events,
            network_graph=event.network_graph,
            is_online=True,
            default_agent_config=event.default_agent_config,
        )
