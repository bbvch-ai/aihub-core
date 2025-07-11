from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.discovery.agent.AgentClassDiscoveryResponseEvent import (
    AgentConfigSpecs,
    AgentClassDiscoveryResponseEvent,
)
from aihub_lib.nats.events.discovery.agent.AgentInstanceDiscoveryResponseEvent import EventSpecs
from aihub_lib.persistence.agents.AgentEntity import AgentEntity
from pydantic import BaseModel, Field

from aihub_api.routes.agent.dto.AgentConfigDTO import AgentConfigDTO


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
            description="A network graph of the agent class, showing how different components are connected and interact.",
        ),
    ]
    is_conversational: Annotated[
        bool, Field(description="Whether the agent class can participate in a chat-based conversation")
    ]
    is_online: Annotated[
        bool | None, Field(description="Indicates whether the agent class is online and reachable.")
    ] = None

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
        )


class MinimalAgentDTO(BaseModel):
    """
    Encapsulates the data transfer object (DTO) for a minimal agent.
    Only contains minimal information about the agent.
    """

    agent_class: Annotated[str, Field(description="The agent's class identifier (e.g., 'my_agent_class').")]
    agent_id: Annotated[str, Field(description="Unique identifier for the agent instance (e.g., 'agent_123').")]
    agent_config: Annotated[
        AgentConfig,
        Field(description="Configuration details of the agent, including name, description, and prompts."),
    ]
    is_conversational: Annotated[
        bool, Field(description="Whether the agent can participate in a chat-based conversation")
    ]

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
            description="A network graph of the agent, showing how different components are connected and interact.",
        ),
    ]
    is_online: Annotated[bool | None, Field(description="Indicates whether the agent is online and reachable.")] = None

    @classmethod
    def from_entity(cls, entity: AgentEntity, t: LocaleHandler, is_online: bool | None = None) -> "AgentDTO":
        """Converts an AgentEntity to an AgentDTO."""
        agent_config_dto = AgentConfigDTO.from_agent_config(entity.agent_config, t)

        start_events = [
            EventSpecs(
                event_name=event.event_name,
                event_schema=event.event_schema,
                event_parents=event.event_parents,
            )
            for event in entity.start_events
        ]

        stop_events = [
            EventSpecs(
                event_name=event.event_name,
                event_schema=event.event_schema,
                event_parents=event.event_parents,
            )
            for event in entity.stop_events
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
            is_online=is_online,
        )

    @classmethod
    def from_class_and_config(cls, class_dto: AgentClassDTO, agent_config: AgentConfig) -> "AgentDTO":
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
        )
