from typing import TYPE_CHECKING, Annotated, Any, Self

from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs
from aihub_lib.persistence.agents.AgentClassEntity import AgentClassEntity
from pydantic import Field

from aihub_api.routes.agent.dto.AgentConfigDTO import AgentConfigDTO
from aihub_api.routes.agent.dto.MinimalAgentInstanceDTO import MinimalAgentInstanceDTO

if TYPE_CHECKING:
    from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument


class FullAgentInstanceDTO(MinimalAgentInstanceDTO):
    """
    A data transfer object for representing FULL agent INSTANCE information in responses.
    This DTO standardizes how agent instance data is returned from the service layer to the controller,
    and subsequently to the API response. It helps maintain a clean separation between the internal
    event models and the publicly exposed fields in HTTP responses.

    NOTE: This represents an INSTANCE (with agent_id), not an agent CLASS.
    For minimal instance data, use MinimalAgentInstanceDTO.
    For class-level data only, use AgentClassDTO.
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
    configuration: Annotated[
        dict[str, Any],
        Field(
            description="The saved configuration data for this agent instance. "
            "Contains the actual values that were submitted via the configuration form.",
        ),
    ] = {}

    @classmethod
    def from_class_and_config(
        cls,
        class_entity: AgentClassEntity,
        config_entity: "AgentConfigEntityDocument",
        t: LocaleHandler,
    ) -> Self:
        """
        Creates a FullAgentInstanceDTO from a class entity and a config entity.
        Class entity provides class-level data (events, graph, form), config entity provides instance data.
        """
        agent_config_dto = AgentConfigDTO.from_class_and_config(class_entity, config_entity, t)

        start_events = [
            EventSpecs(
                event_name=event.event_name,
                event_schema=event.event_schema,
                event_parents=event.event_parents,
            )
            for event in class_entity.start_events
        ]

        stop_events = [
            EventSpecs(
                event_name=event.event_name,
                event_schema=event.event_schema,
                event_parents=event.event_parents,
            )
            for event in class_entity.stop_events
        ]

        hitl_request_events = [
            EventSpecs(
                event_name=event.event_name,
                event_schema=event.event_schema,
                event_parents=event.event_parents,
            )
            for event in class_entity.hitl_request_events
        ]

        hitl_response_events = [
            EventSpecs(
                event_name=event.event_name,
                event_schema=event.event_schema,
                event_parents=event.event_parents,
            )
            for event in class_entity.hitl_response_events
        ]

        network_graph = WorkflowGraph.model_validate(class_entity.network_graph)

        return cls(
            agent_class=class_entity.agent_class,
            agent_id=config_entity.agent_id,
            agent_config=agent_config_dto,
            is_conversational=class_entity.is_conversational,
            start_events=start_events,
            stop_events=stop_events,
            hitl_request_events=hitl_request_events,
            hitl_response_events=hitl_response_events,
            network_graph=network_graph,
            is_online=class_entity.is_online,
            configuration=config_entity.config_data or {},
        )
