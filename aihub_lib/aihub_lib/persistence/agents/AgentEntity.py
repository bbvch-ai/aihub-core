import json
import logging
from datetime import datetime

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
    ReferenceField,
    StringField,
)

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.nats.events.discovery.agent.AgentConfigSpecs import AgentConfigSpecs
from aihub_lib.nats.events.discovery.agent.AgentConfigSpecsEntity import AgentConfigSpecsEntity
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
from aihub_lib.persistence.agents.AgentConfigEntityEmbeddedDocument import AgentConfigEntityEmbeddedDocument

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
    def from_specs(cls, event_specs: EventSpecs) -> "EventSpec":
        """Create an EventSpec from an EventSpecs object."""
        return cls(
            event_name=event_specs.event_name,
            event_schema_json=json.dumps(event_specs.event_schema),
            event_parents=event_specs.event_parents,
        )


class AgentEntity(Document):
    meta = {
        "collection": "agents",
        "strict": False,
        "indexes": [{"fields": ["agent_class", "agent_id"], "unique": True}],
    }
    agent_class = StringField(required=True)
    agent_id = StringField(required=True)
    agent_config = ReferenceField(AgentConfigEntityDocument, required=False)
    default_agent_config = EmbeddedDocumentField(AgentConfigEntityEmbeddedDocument, required=True)
    agent_config_specs = EmbeddedDocumentField(AgentConfigSpecsEntity, required=False)
    is_conversational = BooleanField(required=True)
    start_events = ListField(EmbeddedDocumentField(EventSpec), required=True)
    stop_events = ListField(EmbeddedDocumentField(EventSpec), required=True)
    hitl_request_events = ListField(EmbeddedDocumentField(EventSpec), default=list)
    hitl_response_events = ListField(EmbeddedDocumentField(EventSpec), default=list)
    network_graph = DictField(required=True)
    first_discovered = DateTimeField(required=True, default=datetime.now)
    last_discovered = DateTimeField(required=True, default=datetime.now)

    @classmethod
    @trace_fn
    def create_agent(
        cls,
        agent_class: str,
        agent_id: str,
        agent_config: AgentConfigEntityDocument | None,
        default_agent_config: AgentConfigEntityEmbeddedDocument,
        agent_config_specs: AgentConfigSpecsEntity | None,
        is_conversational: bool,
        start_events: list[EventSpec],
        stop_events: list[EventSpec],
        hitl_request_events: list[EventSpec],
        hitl_response_events: list[EventSpec],
        network_graph: dict,
        agent_entity_id: ObjectId | None = None,
    ) -> "AgentEntity":
        agent = cls(
            id=agent_entity_id or ObjectId(),
            agent_class=agent_class,
            agent_id=agent_id,
            agent_config=agent_config,
            default_agent_config=default_agent_config,
            agent_config_specs=agent_config_specs,
            is_conversational=is_conversational,
            start_events=start_events,
            stop_events=stop_events,
            hitl_request_events=hitl_request_events,
            hitl_response_events=hitl_response_events,
            network_graph=network_graph,
            first_discovered=datetime.now(),
            last_discovered=datetime.now(),
        )
        agent.save()
        return agent

    @classmethod
    @trace_fn
    def create_or_update(
        cls,
        agent_id: str,
        agent_class: str,
        default_agent_config: AgentConfig,
        agent_config_specs: AgentConfigSpecs,
        is_conversational: bool,
        start_events: list[EventSpecs],
        stop_events: list[EventSpecs],
        hitl_request_events: list[EventSpecs],
        hitl_response_events: list[EventSpecs],
        network_graph: WorkflowGraph,
    ) -> "AgentEntity":
        """
        Creates a new AgentEntity from an AgentDTO or updates an existing one if an agent
        with the same agent_class and agent_id already exists.
        """
        # Check if an agent with the same agent_class and agent_id already exists
        existing_agent = cls.objects(agent_class=agent_class, agent_id=agent_id).first()

        agent_config_entity = AgentConfigEntityDocument.find_for_class_and_id(
            agent_class=agent_class, agent_id=agent_id
        )
        if not agent_config_entity:
            logger.debug(f"No agent config found for class {agent_class} and ID {agent_id}.")

        default_agent_config_entity = AgentConfigEntityEmbeddedDocument.from_agent_config(default_agent_config)
        agent_config_specs_entity = AgentConfigSpecsEntity.from_specs(agent_config_specs)

        # Create EventSpec objects, serializing the schema to avoid $ issues
        start_events = [EventSpec.from_specs(event) for event in start_events]
        stop_events = [EventSpec.from_specs(event) for event in stop_events]
        hitl_request_events = [EventSpec.from_specs(event) for event in hitl_request_events]
        hitl_response_events = [EventSpec.from_specs(event) for event in hitl_response_events]

        network_graph = network_graph.model_dump()

        if existing_agent:
            # Update existing agent
            existing_agent.agent_config = agent_config_entity
            existing_agent.default_agent_config = default_agent_config_entity
            existing_agent.agent_config_specs = agent_config_specs_entity
            existing_agent.is_conversational = is_conversational
            existing_agent.start_events = start_events
            existing_agent.stop_events = stop_events
            existing_agent.hitl_request_events = hitl_request_events
            existing_agent.hitl_response_events = hitl_response_events
            existing_agent.network_graph = network_graph
            existing_agent.last_discovered = datetime.now()
            existing_agent.save()
            return existing_agent
        else:
            # Create new agent
            return cls.create_agent(
                agent_class=agent_class,
                agent_id=agent_id,
                agent_config=agent_config_entity,
                default_agent_config=default_agent_config_entity,
                agent_config_specs=agent_config_specs_entity,
                is_conversational=is_conversational,
                start_events=start_events,
                stop_events=stop_events,
                hitl_request_events=hitl_request_events,
                hitl_response_events=hitl_response_events,
                network_graph=network_graph,
            )

    @classmethod
    @trace_fn
    def get_agents(cls):
        return cls.objects()

    @classmethod
    @trace_fn
    def get_agent_by_id(cls, agent_entity_id: str) -> "AgentEntity":
        return cls.objects().get(id=ObjectId(agent_entity_id))

    @classmethod
    @trace_fn
    def get_agent(cls, agent_class: str, agent_id: str) -> "AgentEntity":
        return cls.objects(agent_class=agent_class, agent_id=agent_id).first()
