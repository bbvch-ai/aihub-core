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
    ListField,
    StringField,
)
from pydantic import TypeAdapter

from swiss_ai_hub.core.events.agent.discovery.agent_class_discovery_response_event import (
    AgentClassDiscoveryResponseEvent,
)
from swiss_ai_hub.core.events.agent.discovery.agent_config_specs_entity import AgentConfigSpecsEntity
from swiss_ai_hub.core.events.discovery.event_specs import EventSpecs
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity

if TYPE_CHECKING:
    from swiss_ai_hub.core.form.base.formkit_element import FormkitElement

logger = logging.getLogger(__name__)


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
    # Defaulted, unlike is_conversational: classes discovered before this field existed have no stored
    # value, and reads must not yield None into the non-optional DTO field. Self-heals on next discovery.
    is_schedulable = BooleanField(required=True, default=False)
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
        is_schedulable: bool,
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
            is_schedulable=is_schedulable,
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
    def create_or_update(cls, discovery: AgentClassDiscoveryResponseEvent) -> Self:
        """
        Creates a new AgentClassEntity or updates an existing one if an agent
        with the same agent_class already exists.

        Takes the discovery response wholesale rather than its fields one by one: registering a class
        means recording exactly what the agent reported, so every field arrives from the same event.
        """
        existing_agent = cls.objects(agent_class=discovery.agent_class).first()

        name_entity = LocaleStringEntity.from_locale_string(discovery.name)
        description_entity = LocaleStringEntity.from_locale_string(discovery.description)

        # Store WITHOUT aliases - MongoDB doesn't allow keys starting with '$'
        # Alias conversion happens in the API layer when serving to frontend
        form_dicts = [element.model_dump() for element in discovery.form]
        agent_config_specs_entity = AgentConfigSpecsEntity.from_specs(discovery.agent_config_specs)

        start_events_entities = [EventSpec.from_specs(event) for event in discovery.start_events]
        stop_events_entities = [EventSpec.from_specs(event) for event in discovery.stop_events]
        hitl_request_events_entities = [EventSpec.from_specs(event) for event in discovery.hitl_request_events]
        hitl_response_events_entities = [EventSpec.from_specs(event) for event in discovery.hitl_response_events]

        network_graph_dict = discovery.network_graph.model_dump()
        template_dicts = [template.model_dump() for template in discovery.templates]

        if existing_agent:
            existing_agent.name = name_entity
            existing_agent.description = description_entity
            existing_agent.icon = discovery.icon
            existing_agent.form = form_dicts
            existing_agent.agent_config_specs = agent_config_specs_entity
            existing_agent.is_conversational = discovery.is_conversational
            existing_agent.is_schedulable = discovery.is_schedulable
            existing_agent.start_events = start_events_entities
            existing_agent.stop_events = stop_events_entities
            existing_agent.hitl_request_events = hitl_request_events_entities
            existing_agent.hitl_response_events = hitl_response_events_entities
            existing_agent.network_graph = network_graph_dict
            existing_agent.templates = template_dicts
            existing_agent.last_discovered = datetime.now()
            existing_agent.save()
            return existing_agent
        else:
            return cls.create_agent_class(
                agent_class=discovery.agent_class,
                name=name_entity,
                description=description_entity,
                icon=discovery.icon,
                form=form_dicts,
                agent_config_specs=agent_config_specs_entity,
                is_conversational=discovery.is_conversational,
                is_schedulable=discovery.is_schedulable,
                start_events=start_events_entities,
                stop_events=stop_events_entities,
                hitl_request_events=hitl_request_events_entities,
                hitl_response_events=hitl_response_events_entities,
                network_graph=network_graph_dict,
                templates=template_dicts,
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
    def get_online_schedulable(cls) -> list["AgentClassEntity"]:
        """Schedulable classes currently online — the scheduler only fires runs an agent can consume."""
        threshold = datetime.now() - cls.ONLINE_THRESHOLD
        return list(cls.objects(is_schedulable=True, last_discovered__gte=threshold))

    @classmethod
    @trace_fn
    def get_all_schedulable(cls) -> list["AgentClassEntity"]:
        """Every schedulable class, online or not, for a caller that needs both halves.

        The scheduler needs online and offline classes on the same tick — one set to fire, the other to
        report what it dropped. Fetching them together and splitting in Python costs one round-trip
        instead of two, on a query that runs inside the API process every tick.
        """
        return list(cls.objects(is_schedulable=True))

    @classmethod
    def is_online_at(cls, entity: "AgentClassEntity", now: datetime) -> bool:
        """Whether `entity` counts as online, using the same threshold as the online/offline queries.

        `now` is naive because `last_discovered` is written naive; passing an aware value here would
        compare across timezones and silently classify every class as offline.
        """
        return entity.last_discovered >= now - cls.ONLINE_THRESHOLD

    @classmethod
    @trace_fn
    def get_offline_schedulable(cls) -> list["AgentClassEntity"]:
        """Schedulable classes with no runner online — the exact complement of `get_online_schedulable`.

        The scheduler needs these to report the occurrences it drops rather than queues, which it cannot
        do from the online set alone.
        """
        threshold = datetime.now() - cls.ONLINE_THRESHOLD
        return list(cls.objects(is_schedulable=True, last_discovered__lt=threshold))

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
