from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs
from aihub_lib.persistence.agents.AgentEntity import AgentEntity
from pydantic import Field

from aihub_api.routes.agent.dto.AgentConfigDTO import AgentConfigDTO
from aihub_api.routes.agent.dto.AgentInstanceDTO import AgentInstanceDTO
from aihub_api.routes.agent.dto.MinimalAgentDTO import MinimalAgentDTO


class AgentDTO(MinimalAgentDTO):
    """
    A data transfer object for representing agent information in responses.
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
    hitl_request_events: Annotated[
        list[EventSpecs],
        Field(
            description="A list of `EventSpecs` representing human-in-the-loop request events this agent can produce."
        ),
    ]
    hitl_response_events: Annotated[
        list[EventSpecs],
        Field(
            description="A list of `EventSpecs` representing human-in-the-loop response events this agent can accept."
        ),
    ]
    network_graph: Annotated[
        WorkflowGraph,
        Field(
            description="A network graph of the agent, showing how different components are connected and interact.",
        ),
    ]
    is_online: Annotated[bool | None, Field(description="Indicates whether the agent is online and reachable.")] = None

    @classmethod
    def from_instance(cls, instance: AgentInstanceDTO, t: LocaleHandler, is_online: bool | None = None) -> "AgentDTO":
        """Creates an AgentDTO from an AgentInstanceDTO."""
        return cls(
            agent_class=instance.agent_class,
            agent_id=instance.agent_id,
            agent_config=AgentConfigDTO.from_agent_config(instance.agent_config or instance.default_agent_config, t),
            is_conversational=instance.is_conversational,
            start_events=instance.start_events,
            stop_events=instance.stop_events,
            hitl_request_events=instance.hitl_request_events,
            hitl_response_events=instance.hitl_response_events,
            network_graph=instance.network_graph,
            is_online=is_online,
        )

    @classmethod
    def from_entity(cls, entity: AgentEntity, t: LocaleHandler) -> "AgentDTO":
        """Converts an AgentEntity to an AgentDTO. Online status is derived from entity.last_discovered."""
        agent_config = AgentConfig.from_entity(entity.agent_config or entity.default_agent_config)
        agent_config_dto = AgentConfigDTO.from_agent_config(agent_config, t)

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

        hitl_request_events = [
            EventSpecs(
                event_name=event.event_name,
                event_schema=event.event_schema,
                event_parents=event.event_parents,
            )
            for event in entity.hitl_request_events
        ]

        hitl_response_events = [
            EventSpecs(
                event_name=event.event_name,
                event_schema=event.event_schema,
                event_parents=event.event_parents,
            )
            for event in entity.hitl_response_events
        ]

        network_graph = WorkflowGraph.model_validate(entity.network_graph)

        return cls(
            agent_class=entity.agent_class,
            agent_id=entity.agent_id,
            agent_config=agent_config_dto,
            is_conversational=entity.is_conversational,
            start_events=start_events,
            stop_events=stop_events,
            hitl_request_events=hitl_request_events,
            hitl_response_events=hitl_response_events,
            network_graph=network_graph,
            is_online=entity.is_online,
        )
