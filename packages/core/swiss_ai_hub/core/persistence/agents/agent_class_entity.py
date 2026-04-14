import json
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Self

from bson import ObjectId
from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    IntField,
    ListField,
    StringField,
)
from pydantic import TypeAdapter

from swiss_ai_hub.core.agents.visualizers.types.workflow_graph import WorkflowGraph
from swiss_ai_hub.core.events.agent.discovery.agent_config_specs import AgentConfigSpecs
from swiss_ai_hub.core.events.agent.discovery.agent_config_specs_entity import AgentConfigSpecsEntity
from swiss_ai_hub.core.events.discovery.event_specs import EventSpecs
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity

if TYPE_CHECKING:
    from swiss_ai_hub.core.form.base.formkit_element import FormkitElement

logger = logging.getLogger(__name__)


class EventPayloadField(EmbeddedDocument):
    """Information about an event payload field."""

    type = StringField(required=True)
    description = StringField()


class EventInfo(EmbeddedDocument):
    """Information about an event."""

    name = StringField(required=True)
    full_name = StringField(required=True)
    is_start_event = BooleanField(required=True)
    is_stop_event = BooleanField(required=True)
    payload = DictField(required=True)  # dict[str, EventPayloadField]


class InputEventInfo(EmbeddedDocument):
    """Information about an input event for a step."""

    event_names = ListField(EmbeddedDocumentField(EventInfo), required=True)
    optional = BooleanField(required=True)


class NodeData(EmbeddedDocument):
    """Data for a node in the workflow graph."""

    id = StringField(required=True)
    type = StringField(required=True)
    node_id = StringField(required=True)
    label = StringField(required=True)
    description = StringField()
    icon = StringField()
    input_events = DictField(field=EmbeddedDocumentField(InputEventInfo))  # dict[str, InputEventInfo]
    output_events = ListField(EmbeddedDocumentField(EventInfo))
    max_executions = IntField()
    stop_on_error = BooleanField()


class EdgeData(EmbeddedDocument):
    """Data for an edge in the workflow graph."""

    source = StringField(required=True)
    target = StringField(required=True)
    edge_id = IntField(required=True)
    event_name = StringField(required=True)
    event_full_name = StringField(required=True)
    is_start_event = BooleanField(required=True)
    is_stop_event = BooleanField(required=True)
    payload = DictField(required=True)  # dict[str, EventPayloadField]


class EventSpec(EmbeddedDocument):
    """Information about an event specification."""

    event_name = StringField(required=True)
    event_schema_json = StringField(required=True)  # Store as JSON string to avoid issues with $ in keys
    event_parents = ListField(StringField(), default=list)

    @property
    def event_schema(self):
        """Deserialize the event schema from JSON string to dictionary."""
        return json.loads(self.event_schema_json)

    @classmethod
    def from_specs(cls, event_specs: EventSpecs) -> Self:
        """Create an EventSpec from an EventSpecs object."""
        return cls(
            event_name=event_specs.event_name,
            event_schema_json=json.dumps(event_specs.event_schema),
            event_parents=event_specs.event_parents,
        )

    def to_specs(self) -> EventSpecs:
        """Convert this entity back to an EventSpecs Pydantic model."""
        return EventSpecs(
            event_name=self.event_name,
            event_schema=self.event_schema,
            event_parents=self.event_parents,
        )


class AgentClassEntity(Document):
    """
    Represents a registered agent CLASS in the system.

    Stores the class-level metadata (name, description, icon), form schema for
    creating agent instances, and the validation specs.
    Online status is determined by the last_discovered timestamp.

    NOTE: This entity stores CLASS information only (one record per agent_class).
    Instance/configuration data is stored in AgentConfigEntityDocument.
    """

    ONLINE_THRESHOLD = timedelta(minutes=5)

    meta = {
        "collection": "agent_classes",
        "strict": False,
        "indexes": [
            {"fields": ["agent_class"], "unique": True},
        ],
    }
    agent_class = StringField(required=True, unique=True)

    # Class-level metadata (describes the agent class itself, not instances)
    name = EmbeddedDocumentField(LocaleStringEntity, required=False, description="Display name for this agent class.")
    description = EmbeddedDocumentField(
        LocaleStringEntity, required=False, description="Description of this agent class."
    )
    icon = StringField(required=True, default="mage:robot", description="Icon for this agent class.")

    form = ListField(DictField(), default=list, description="FormKit elements defining the agent configuration form.")
    agent_config_specs = EmbeddedDocumentField(AgentConfigSpecsEntity, required=False)
    is_conversational = BooleanField(required=True)
    start_events = ListField(EmbeddedDocumentField(EventSpec), required=True)
    stop_events = ListField(EmbeddedDocumentField(EventSpec), required=True)
    hitl_request_events = ListField(EmbeddedDocumentField(EventSpec), default=list)
    hitl_response_events = ListField(EmbeddedDocumentField(EventSpec), default=list)
    network_graph = DictField(required=True)
    templates = ListField(DictField(), default=list)
    first_discovered = DateTimeField(required=True, default=datetime.now)
    last_discovered = DateTimeField(required=True, default=datetime.now)

    @property
    def is_online(self) -> bool:
        """Agent is online if it responded to discovery within the threshold."""
        if self.last_discovered is None:
            return False
        return datetime.now() - self.last_discovered < self.ONLINE_THRESHOLD

    @property
    def form_elements(self) -> list["FormkitElement"]:
        """Deserialize the stored form dicts back to typed form element Pydantic models."""
        if not self.form:
            return []
        adapter = TypeAdapter(list[ALL_FORM_OPTIONS])
        return adapter.validate_python(self.form)

    @classmethod
    @trace_fn
    def create_agent_class(
        cls,
        agent_class: str,
        name: LocaleStringEntity | None,
        description: LocaleStringEntity | None,
        icon: str,
        form: list[dict],
        agent_config_specs: AgentConfigSpecsEntity | None,
        is_conversational: bool,
        start_events: list[EventSpec],
        stop_events: list[EventSpec],
        hitl_request_events: list[EventSpec],
        hitl_response_events: list[EventSpec],
        network_graph: dict,
        templates: list[dict] | None = None,
        agent_class_entity_id: ObjectId | None = None,
    ) -> Self:
        agent = cls(
            id=agent_class_entity_id or ObjectId(),
            agent_class=agent_class,
            name=name,
            description=description,
            icon=icon,
            form=form,
            agent_config_specs=agent_config_specs,
            is_conversational=is_conversational,
            start_events=start_events,
            stop_events=stop_events,
            hitl_request_events=hitl_request_events,
            hitl_response_events=hitl_response_events,
            network_graph=network_graph,
            templates=templates or [],
            first_discovered=datetime.now(),
            last_discovered=datetime.now(),
        )
        agent.save()
        return agent

    @classmethod
    @trace_fn
    def create_or_update(
        cls,
        agent_class: str,
        name: LocaleString,
        description: LocaleString,
        icon: str,
        form: list[ALL_FORM_OPTIONS],
        agent_config_specs: AgentConfigSpecs,
        is_conversational: bool,
        start_events: list[EventSpecs],
        stop_events: list[EventSpecs],
        hitl_request_events: list[EventSpecs],
        hitl_response_events: list[EventSpecs],
        network_graph: WorkflowGraph,
        templates: list[dict] | None = None,
    ) -> Self:
        """
        Creates a new AgentClassEntity or updates an existing one if an agent
        with the same agent_class already exists.
        """
        existing_agent = cls.objects(agent_class=agent_class).first()

        name_entity = LocaleStringEntity.from_locale_string(name)
        description_entity = LocaleStringEntity.from_locale_string(description)

        # Store WITHOUT aliases - MongoDB doesn't allow keys starting with '$'
        # Alias conversion happens in the API layer when serving to frontend
        form_dicts = [element.model_dump() for element in form]
        agent_config_specs_entity = AgentConfigSpecsEntity.from_specs(agent_config_specs)

        start_events_entities = [EventSpec.from_specs(event) for event in start_events]
        stop_events_entities = [EventSpec.from_specs(event) for event in stop_events]
        hitl_request_events_entities = [EventSpec.from_specs(event) for event in hitl_request_events]
        hitl_response_events_entities = [EventSpec.from_specs(event) for event in hitl_response_events]

        network_graph_dict = network_graph.model_dump()

        if existing_agent:
            existing_agent.name = name_entity
            existing_agent.description = description_entity
            existing_agent.icon = icon
            existing_agent.form = form_dicts
            existing_agent.agent_config_specs = agent_config_specs_entity
            existing_agent.is_conversational = is_conversational
            existing_agent.start_events = start_events_entities
            existing_agent.stop_events = stop_events_entities
            existing_agent.hitl_request_events = hitl_request_events_entities
            existing_agent.hitl_response_events = hitl_response_events_entities
            existing_agent.network_graph = network_graph_dict
            existing_agent.templates = templates or []
            existing_agent.last_discovered = datetime.now()
            existing_agent.save()
            return existing_agent
        else:
            return cls.create_agent_class(
                agent_class=agent_class,
                name=name_entity,
                description=description_entity,
                icon=icon,
                form=form_dicts,
                agent_config_specs=agent_config_specs_entity,
                is_conversational=is_conversational,
                start_events=start_events_entities,
                stop_events=stop_events_entities,
                hitl_request_events=hitl_request_events_entities,
                hitl_response_events=hitl_response_events_entities,
                network_graph=network_graph_dict,
                templates=templates,
            )

    @classmethod
    @trace_fn
    def get_all(cls) -> list["AgentClassEntity"]:
        """Get all registered agent classes."""
        return list(cls.objects())

    @classmethod
    @trace_fn
    def get_online_conversational(cls) -> list["AgentClassEntity"]:
        threshold = datetime.now() - cls.ONLINE_THRESHOLD
        return list(cls.objects(is_conversational=True, last_discovered__gte=threshold))

    @classmethod
    @trace_fn
    def get_by_id(cls, agent_class_entity_id: str) -> Self:
        """Get an agent class by its MongoDB document ID."""
        return cls.objects().get(id=ObjectId(agent_class_entity_id))

    @classmethod
    @trace_fn
    def get_by_agent_class(cls, agent_class: str) -> "AgentClassEntity | None":
        """Get an agent class by its class name."""
        return cls.objects(agent_class=agent_class).first()
