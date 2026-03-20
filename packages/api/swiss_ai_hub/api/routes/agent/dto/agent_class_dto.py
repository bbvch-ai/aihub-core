from typing import TYPE_CHECKING, Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.agents import WorkflowGraph
from swiss_ai_hub.core.events import EventSpecs
from swiss_ai_hub.core.events.agent import AgentClassDiscoveryResponseEvent, AgentConfigSpecs
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS, TemplateData
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString

if TYPE_CHECKING:
    from swiss_ai_hub.core.persistence.agents import AgentClassEntity


class AgentClassDTO(BaseModel):
    """
    Encapsulates the data transfer object (DTO) for an agent class.

    Contains class-level metadata (name, description, icon), the form schema for creating
    agent instances, and the validation specs for form submissions.
    Default values are embedded in the FormKit elements.
    """

    agent_class: Annotated[str, Field(description="The agent's class identifier (e.g., 'my_agent_class').")]
    # Class-level metadata (describes the agent class template itself)
    name: Annotated[LocaleString, Field(description="Display name for this agent class.")]
    description: Annotated[LocaleString, Field(description="Description of this agent class.")]
    icon: Annotated[str, Field(description="Icon for this agent class.")] = "mage:robot"
    form: Annotated[
        list[ALL_FORM_OPTIONS],
        Field(
            description="FormKit elements defining the agent configuration form. "
            "Default values are embedded in the elements themselves.",
        ),
    ]
    agent_config_specs: Annotated[
        AgentConfigSpecs,
        Field(
            description="Validation specification including the JSON schema for form submissions. "
            "Used by ModelCreationService to create Pydantic models for validation.",
        ),
    ]
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
    templates: Annotated[
        list[TemplateData],
        Field(description="List of profile templates for quick profile creation."),
    ] = []

    @classmethod
    def from_discovery_event(
        cls,
        event: AgentClassDiscoveryResponseEvent,
    ) -> Self:
        """Converts an AgentClassDiscoveryResponseEvent to an AgentClassDTO."""
        return cls(
            agent_class=event.agent_class,
            name=event.name,
            description=event.description,
            icon=event.icon,
            form=event.form,
            agent_config_specs=event.agent_config_specs,
            is_conversational=event.is_conversational,
            start_events=event.start_events,
            stop_events=event.stop_events,
            hitl_request_events=event.hitl_request_events,
            hitl_response_events=event.hitl_response_events,
            network_graph=event.network_graph,
            is_online=True,
            templates=event.templates,
        )

    @classmethod
    def from_entity(cls, entity: "AgentClassEntity", t: LocaleHandler) -> Self:
        """Creates an AgentClassDTO from a database entity (for offline classes)."""
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

        name = entity.name.to_locale_string() if entity.name else LocaleString(de=entity.agent_class)
        description = entity.description.to_locale_string() if entity.description else LocaleString(de="")

        agent_config_specs = entity.agent_config_specs.to_specs() if entity.agent_config_specs else None

        dto = cls(
            agent_class=entity.agent_class,
            name=name,
            description=description,
            icon=entity.icon,
            form=entity.form_elements,
            agent_config_specs=agent_config_specs,
            is_conversational=entity.is_conversational,
            start_events=start_events,
            stop_events=stop_events,
            hitl_request_events=hitl_request_events,
            hitl_response_events=hitl_response_events,
            network_graph=network_graph,
            is_online=entity.is_online,
            templates=[TemplateData.model_validate(td) for td in entity.templates] if entity.templates else [],
        )
        return dto.in_locale(t)

    def in_locale(self, t: LocaleHandler) -> Self:
        """Apply locale transformation to form elements (adds * to required labels, translates strings)."""
        localized_form = [form_element.in_locale(t) for form_element in self.form]
        return self.model_copy(update={"form": localized_form})
